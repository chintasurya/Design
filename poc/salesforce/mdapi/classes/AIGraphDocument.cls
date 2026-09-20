/**
 * Layer 5: the vendor-neutral graph contract.
 *
 * This shape is the whole point of the layer. It is not a Salesforce
 * structure, it carries no Salesforce ids, and nothing about it assumes Apex
 * will be the thing reading it. The same file can be handed to Semantica, to
 * Spanner Graph, or to anything else, which is what keeps the runtime
 * replaceable.
 *
 * One file per source, plus a combined file the queries actually read. That
 * way re-syncing Salesforce never touches the Jira graph, and each file can be
 * downloaded and inspected on its own.
 */
public class AIGraphDocument {

    public String version = '1.0';
    public String source;            // SALESFORCE | JIRA | CONFLUENCE | COMBINED
    public String snapshotId;
    public String exportedAt;
    public Integer nodeCount = 0;
    public Integer edgeCount = 0;
    public List<String> notes = new List<String>();

    public List<GraphNode> nodes = new List<GraphNode>();
    public List<GraphEdge> relationships = new List<GraphEdge>();

    /**
     * Wire keys are nodeType and edgeType, not "type". Apex treats "type" as
     * reserved, and Apex JSON serialization takes the key straight from the
     * field name. A consumer expecting the documented "type" key needs a
     * one-line rename; that is cheaper than hand-rolling a JSONGenerator.
     */
    public class GraphNode {
        public String id;
        public String nodeType;
        public String name;
        public String apiName;
        public String properties;
        public String provenance;
        public String riskTier;
        public String sourceSystem;
    }

    /**
     * "from" and "to" are reserved in Apex, hence fromId and toId. The JSON
     * keys follow the field names, so a consumer reads fromId/toId.
     */
    public class GraphEdge {
        public String id;
        public String edgeType;
        public String fromId;
        public String toId;
        public String origin;
        public String provenance;
        public Decimal confidence;
    }

    public GraphNode addNode(String id, String nodeType, String name, String apiName,
                             String properties, String riskTier, String provenance,
                             String sourceSystem) {
        GraphNode n = new GraphNode();
        n.id = id;
        n.nodeType = nodeType;
        n.name = name;
        n.apiName = apiName;
        n.properties = properties;
        n.riskTier = riskTier;
        n.provenance = provenance;
        n.sourceSystem = sourceSystem;
        nodes.add(n);
        nodeCount = nodes.size();
        return n;
    }

    public GraphEdge addEdge(String fromId, String edgeType, String toId,
                             String provenance) {
        GraphEdge e = new GraphEdge();
        e.id = fromId + '|' + edgeType + '|' + toId;
        e.edgeType = edgeType;
        e.fromId = fromId;
        e.toId = toId;
        e.origin = 'FACTUAL';
        e.confidence = 1.0;
        e.provenance = provenance;
        relationships.add(e);
        edgeCount = relationships.size();
        return e;
    }

    /** Merge per-source documents into the file the queries read. */
    public static AIGraphDocument combine(List<AIGraphDocument> parts) {
        AIGraphDocument out = new AIGraphDocument();
        out.source = 'COMBINED';
        out.snapshotId = String.valueOf(System.now().getTime());
        out.exportedAt = System.now().formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\'');

        Set<String> nodeIds = new Set<String>();
        Set<String> edgeIds = new Set<String>();
        for (AIGraphDocument part : parts) {
            if (part == null) {
                continue;
            }
            for (GraphNode n : part.nodes) {
                if (nodeIds.add(n.id)) {
                    out.nodes.add(n);
                }
            }
            for (GraphEdge e : part.relationships) {
                if (edgeIds.add(e.id)) {
                    out.relationships.add(e);
                }
            }
            out.notes.add(part.source + ': ' + part.nodes.size() + ' nodes, '
                + part.relationships.size() + ' edges');
        }
        out.nodeCount = out.nodes.size();
        out.edgeCount = out.relationships.size();
        return out;
    }
}
