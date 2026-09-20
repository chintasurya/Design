/**
 * Layer 7: the in-memory graph.
 *
 * Load the JSON once per transaction, index it into adjacency maps, traverse.
 * That is the same shape as Semantica: a document goes in, typed nodes and
 * edges with O(1) lookup come out, and traversal walks pointers rather than
 * querying anything.
 *
 * Heap is the binding constraint. Peak is roughly 5.5x the JSON size once you
 * count the blob, the UTF-16 string and the deserialized tree:
 *
 *    1.0 MB JSON  ~5.5 MB peak   fits sync (6 MB) and async (12 MB)
 *    1.7 MB JSON  ~9.2 MB peak   async only
 *    3.0 MB JSON  ~16 MB peak    fits nowhere
 *
 * So the practical ceiling is about 5,000 nodes and 12,500 edges, which is one
 * properly scoped pod. It is not a tuning knob: the whole org at 36,330 nodes
 * would need roughly 60 MB and simply cannot be loaded.
 */
public with sharing class AIGraphMemory {

    public String snapshotId;
    public String exportedAt;
    public Integer nodeCount = 0;
    public Integer edgeCount = 0;
    public List<String> notes = new List<String>();

    /** Heap consumed by loading and indexing, measured rather than estimated. */
    public Integer heapUsedBytes = 0;
    public Integer heapLimitBytes = 0;

    public String heapNote() {
        if (heapLimitBytes == 0) {
            return '';
        }
        return String.valueOf(heapUsedBytes / 1048576) + '.'
             + String.valueOf((heapUsedBytes * 10 / 1048576) - (heapUsedBytes / 1048576) * 10)
             + ' of ' + (heapLimitBytes / 1048576) + ' MB heap';
    }

    private Map<String, AIGraphDocument.GraphNode> nodesById =
        new Map<String, AIGraphDocument.GraphNode>();
    private Map<String, List<AIGraphDocument.GraphEdge>> outgoing =
        new Map<String, List<AIGraphDocument.GraphEdge>>();
    private Map<String, List<AIGraphDocument.GraphEdge>> incoming =
        new Map<String, List<AIGraphDocument.GraphEdge>>();

    public class Hit {
        public AIGraphDocument.GraphNode node;
        public Integer hops;
        public String path;
    }

    // ------------------------------------------------------------- loading

    public static AIGraphMemory load(String fileName) {
        Integer before = Limits.getHeapSize();
        AIGraphDocument doc = AIGraphFileStore.load(fileName);
        if (doc == null) {
            return null;
        }
        AIGraphMemory g = fromDocument(doc);
        g.heapUsedBytes = Limits.getHeapSize() - before;
        g.heapLimitBytes = Limits.getLimitHeapSize();
        return g;
    }

    public static AIGraphMemory fromDocument(AIGraphDocument doc) {
        AIGraphMemory g = new AIGraphMemory();
        g.snapshotId = doc.snapshotId;
        g.exportedAt = doc.exportedAt;
        g.notes = doc.notes == null ? new List<String>() : doc.notes;

        for (AIGraphDocument.GraphNode n : doc.nodes) {
            g.nodesById.put(n.id, n);
        }
        for (AIGraphDocument.GraphEdge e : doc.relationships) {
            if (!g.outgoing.containsKey(e.fromId)) {
                g.outgoing.put(e.fromId, new List<AIGraphDocument.GraphEdge>());
            }
            g.outgoing.get(e.fromId).add(e);
            if (!g.incoming.containsKey(e.toId)) {
                g.incoming.put(e.toId, new List<AIGraphDocument.GraphEdge>());
            }
            g.incoming.get(e.toId).add(e);
        }
        g.nodeCount = g.nodesById.size();
        g.edgeCount = doc.relationships.size();
        return g;
    }

    public AIGraphDocument.GraphNode getNode(String nodeId) {
        return nodesById.get(nodeId);
    }

    // -------------------------------------------------------------- seeding

    /**
     * The object the request names, if the graph holds it. This is the
     * strongest possible seed and beats any keyword.
     */
    public List<AIGraphDocument.GraphNode> anchorObject(String objectName) {
        List<AIGraphDocument.GraphNode> out = new List<AIGraphDocument.GraphNode>();
        if (String.isBlank(objectName)) {
            return out;
        }
        String wanted = flatten(objectName);
        for (AIGraphDocument.GraphNode n : nodesById.values()) {
            if (n.nodeType != 'SObject') {
                continue;
            }
            if (flatten(n.apiName) == wanted || flatten(n.name) == wanted) {
                out.add(n);
                return out;
            }
        }
        return out;
    }

    /**
     * Split a name into whole words, including camel case boundaries, so that
     * matching can respect word edges.
     *
     * "ACC Update Date On Chat Transcript" -> ACC UPDATE DATE ON CHAT TRANSCRIPT
     * "HealthcareFacility"                 -> HEALTHCARE FACILITY HEALTHCAREFACILITY
     */
    @TestVisible
    private static Set<String> wordsOf(String value) {
        Set<String> words = new Set<String>();
        if (String.isBlank(value)) {
            return words;
        }
        String spaced = value.replaceAll('([a-z0-9])([A-Z])', '$1 $2');
        for (String w : spaced.toUpperCase().split('[^A-Z0-9]+')) {
            if (w.length() > 1) {
                words.add(w);
            }
        }
        words.add(flatten(value));
        return words;
    }

    private static String flatten(String value) {
        return value == null ? '' : value.toUpperCase().replaceAll('[^A-Z0-9]', '');
    }

    /** Nodes with a whole word matching a term. The traversal starts here. */
    public List<AIGraphDocument.GraphNode> seeds(Set<String> terms,
                                                 String preferredType,
                                                 Integer maxSeeds) {
        List<AIGraphDocument.GraphNode> preferred =
            new List<AIGraphDocument.GraphNode>();
        List<AIGraphDocument.GraphNode> rest =
            new List<AIGraphDocument.GraphNode>();
        if (terms == null || terms.isEmpty()) {
            return preferred;
        }

        for (AIGraphDocument.GraphNode n : nodesById.values()) {
            // Whole words, not substrings. A plain contains() made the term
            // "DATE" match every flow whose name held the word "Update",
            // because UPDATE contains DATE.
            Set<String> words = wordsOf(n.apiName);
            words.addAll(wordsOf(n.name));
            Boolean hit = false;
            for (String t : terms) {
                if (words.contains(t)) {
                    hit = true;
                    break;
                }
            }
            if (!hit) {
                continue;
            }
            if (String.isNotBlank(preferredType) && n.nodeType == preferredType) {
                preferred.add(n);
            } else {
                rest.add(n);
            }
            if (preferred.size() >= maxSeeds) {
                break;
            }
        }
        for (AIGraphDocument.GraphNode n : rest) {
            if (preferred.size() >= maxSeeds) {
                break;
            }
            preferred.add(n);
        }
        return preferred;
    }

    // ------------------------------------------------------------ traversal

    /**
     * Everything reachable from the seeds within maxHops, both directions.
     *
     * Direction matters. A Flow edge points AT the object it updates, so
     * "what touches this object" has to follow incoming edges as well, or the
     * automation that actually writes to it never appears.
     */
    public List<Hit> blastRadius(List<String> seedIds, Integer maxHops,
                                 Integer maxNodes) {
        List<Hit> hits = new List<Hit>();
        if (seedIds == null || seedIds.isEmpty()) {
            return hits;
        }
        Set<String> visited = new Set<String>(seedIds);
        Set<String> frontier = new Set<String>(seedIds);
        Map<String, Integer> hopOf = new Map<String, Integer>();
        Map<String, String> pathOf = new Map<String, String>();
        for (String s : seedIds) {
            hopOf.put(s, 0);
        }

        for (Integer hop = 1; hop <= maxHops && !frontier.isEmpty(); hop++) {
            Set<String> next = new Set<String>();
            for (String current : frontier) {
                for (AIGraphDocument.GraphEdge e : edgesTouching(current)) {
                    String other = e.fromId == current ? e.toId : e.fromId;
                    if (!visited.add(other)) {
                        continue;
                    }
                    next.add(other);
                    hopOf.put(other, hop);
                    pathOf.put(other,
                        e.fromId + ' -[' + e.edgeType + ']-> ' + e.toId);
                    if (visited.size() >= maxNodes) {
                        break;
                    }
                }
                if (visited.size() >= maxNodes) {
                    break;
                }
            }
            if (visited.size() >= maxNodes) {
                break;
            }
            frontier = next;
        }

        for (String nodeId : visited) {
            AIGraphDocument.GraphNode n = nodesById.get(nodeId);
            if (n == null) {
                continue;
            }
            Hit h = new Hit();
            h.node = n;
            h.hops = hopOf.containsKey(nodeId) ? hopOf.get(nodeId) : 0;
            h.path = pathOf.containsKey(nodeId)
                   ? pathOf.get(nodeId) : 'Matched the request directly';
            hits.add(h);
        }
        return hits;
    }

    private List<AIGraphDocument.GraphEdge> edgesTouching(String nodeId) {
        List<AIGraphDocument.GraphEdge> all =
            new List<AIGraphDocument.GraphEdge>();
        if (outgoing.containsKey(nodeId)) {
            all.addAll(outgoing.get(nodeId));
        }
        if (incoming.containsKey(nodeId)) {
            all.addAll(incoming.get(nodeId));
        }
        return all;
    }

    /** Counts by node type and edge type, for the console status bar. */
    public Map<String, Object> stats() {
        Map<String, Integer> byNodeType = new Map<String, Integer>();
        for (AIGraphDocument.GraphNode n : nodesById.values()) {
            Integer c = byNodeType.containsKey(n.nodeType)
                      ? byNodeType.get(n.nodeType) : 0;
            byNodeType.put(n.nodeType, c + 1);
        }
        Map<String, Integer> byEdgeType = new Map<String, Integer>();
        for (List<AIGraphDocument.GraphEdge> edgeList : outgoing.values()) {
            for (AIGraphDocument.GraphEdge e : edgeList) {
                Integer c = byEdgeType.containsKey(e.edgeType)
                          ? byEdgeType.get(e.edgeType) : 0;
                byEdgeType.put(e.edgeType, c + 1);
            }
        }
        return new Map<String, Object>{
            'nodes' => nodeCount,
            'edges' => edgeCount,
            'byNodeType' => byNodeType,
            'byEdgeType' => byEdgeType,
            'snapshotId' => snapshotId,
            'exportedAt' => exportedAt
        };
    }
}
