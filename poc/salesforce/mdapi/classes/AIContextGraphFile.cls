/**
 * Layer 8 adapter: context slices from the file-backed graph.
 *
 * Loads the combined document, indexes it, traverses. Nothing queries the org
 * at request time; every relationship was resolved when the graph was
 * exported, which is what lets this answer at depth.
 */
public with sharing class AIContextGraphFile implements AIContextGraphService {

    private static final Integer MAX_SEEDS = 6;
    private static final Integer MAX_NODES = 60;

    public AIContextSlice query(AI_Change_Request__c request) {
        AIContextSlice slice = new AIContextSlice();
        AIRequestIntent intent = AIRequestIntent.parse(request.Request_Text__c);

        AIGraphMemory graph;
        try {
            graph = AIGraphMemory.load(AIGraphFileStore.COMBINED);
        } catch (System.LimitException e) {
            slice.snapshotId = 'none';
            slice.summary = 'The graph is too large to load in this context. '
                + 'It must be narrowed, or the search moved to an asynchronous '
                + 'job where the heap limit is 12 MB rather than 6 MB. '
                + e.getMessage();
            return slice;
        }
        if (graph == null) {
            slice.snapshotId = 'none';
            slice.summary = 'The knowledge graph has not been exported yet. '
                + 'Run Build graph, then ask again.';
            return slice;
        }
        slice.snapshotId = graph.snapshotId;

        // The named object is the anchor. Keywords only seed when no object
        // was named or the graph does not hold it, because a generic word like
        // "date" otherwise drags in unrelated automation from across the org.
        List<AIGraphDocument.GraphNode> seeds =
            graph.anchorObject(intent.targetObject);
        String seedBasis = 'object ' + intent.targetObject;

        // A behaviour question is answered from the trigger object or not at
        // all. Falling back to keywords here seeds on whatever else the
        // sentence mentions, finds no automation, and the absence then reads
        // as a clearance. Say the object is missing instead.
        if (seeds.isEmpty() && intent.requestShape == 'Behaviour'
                && String.isNotBlank(intent.triggerObject)) {
            slice.summary = 'Read: ' + intent.summary
                + ' · the graph does not hold ' + intent.triggerObject
                + ', so what already runs on it is unknown. It is outside the '
                + 'pod scope, or the graph predates it. ' + graph.nodeCount
                + ' nodes searched · ' + graph.heapNote();
            return slice;
        }

        if (seeds.isEmpty()) {
            Set<String> terms = new Set<String>(intent.terms);
            if (String.isNotBlank(intent.targetName)) {
                terms.addAll(
                    AISalesforceMetadataSource.extractTerms(intent.targetName));
            }
            // A declared data type describes the field, it does not name a
            // component, so it must not pull in matches of its own.
            if (String.isNotBlank(intent.targetDataType)) {
                terms.remove(intent.targetDataType.toUpperCase());
            }
            seeds = graph.seeds(terms, intent.targetType, MAX_SEEDS);
            seedBasis = 'keywords ' + String.join(new List<String>(terms), ', ');
        }
        if (seeds.isEmpty()) {
            slice.summary = 'Read: ' + intent.summary
                + ' · nothing matched in the graph (' + graph.nodeCount
                + ' nodes searched, tried ' + seedBasis + ')';
            return slice;
        }

        List<String> seedIds = new List<String>();
        for (AIGraphDocument.GraphNode n : seeds) {
            seedIds.add(n.id);
        }

        Integer hops = intent.action == 'Create' ? 1 : 3;

        // Columns are not behaviour. Excluded here rather than in relevant()
        // below, because by then they have already spent the node budget and
        // the automation that answers the question never entered the walk.
        Set<String> skipTypes = null;
        if (intent.requestShape == 'Behaviour') {
            skipTypes = new Set<String>{ 'Field', 'RecordType' };
        }
        List<AIGraphMemory.Hit> hits =
            graph.blastRadius(seedIds, hops, MAX_NODES, skipTypes);
        Integer beforeFilter = hits.size();

        for (AIGraphMemory.Hit h : relevant(hits, intent)) {
            slice.findings.add(AIContextSlice.build(
                h.node.id, h.node.nodeType, h.node.name, h.path,
                impactOf(h.hops), h.node.riskTier, h.node.sourceSystem,
                h.node.provenance));
        }
        Integer dropped = beforeFilter - slice.findings.size();

        slice.summary = 'Read: ' + intent.summary
            + ' · traversed ' + hops + ' hop' + (hops == 1 ? '' : 's')
            + ' from ' + seedBasis
            + ' across ' + graph.nodeCount + ' nodes and ' + graph.edgeCount
            + ' edges · ' + slice.findings.size() + ' relevant'
            + (dropped > 0 ? ' (' + dropped + ' unrelated hidden)' : '')
            + ' · ' + graph.heapNote();
        return slice;
    }

    /**
     * Keep what bears on the question, drop the rest.
     *
     * Asking whether one field exists returned 54 components, because an
     * object drags in every field it has. The answer to "does this field
     * exist" is the matching field plus the automation that would need
     * regression, not a directory of the object.
     */
    private static List<AIGraphMemory.Hit> relevant(List<AIGraphMemory.Hit> hits,
                                                    AIRequestIntent intent) {
        List<AIGraphMemory.Hit> keep = new List<AIGraphMemory.Hit>();
        Set<String> wanted = new Set<String>();
        if (String.isNotBlank(intent.targetName)) {
            for (String w : intent.targetName.toUpperCase().split('[^A-Z0-9]+')) {
                if (w.length() > 2) {
                    wanted.add(w);
                }
            }
        }

        for (AIGraphMemory.Hit h : hits) {
            String nodeType = h.node.nodeType;

            // Automation and the anchor object always matter.
            if (nodeType != 'Field' && nodeType != 'RecordType') {
                keep.add(h);
                continue;
            }
            // A behaviour request is about what runs, not about columns.
            if (intent.requestShape == 'Behaviour') {
                continue;
            }
            // Otherwise a field earns its place by relating to what was asked.
            if (wanted.isEmpty()) {
                keep.add(h);
                continue;
            }
            Set<String> words = new Set<String>();
            for (String w : ((h.node.apiName == null ? '' : h.node.apiName) + ' '
                    + (h.node.name == null ? '' : h.node.name))
                    .replaceAll('([a-z0-9])([A-Z])', '$1 $2')
                    .toUpperCase().split('[^A-Z0-9]+')) {
                words.add(w);
            }
            for (String w : wanted) {
                if (words.contains(w)) {
                    keep.add(h);
                    break;
                }
            }
        }
        return keep;
    }

    private static String impactOf(Integer hops) {
        if (hops == 0) { return 'Direct'; }
        if (hops == 1) { return 'One Hop'; }
        if (hops == 2) { return 'Two Hop'; }
        return 'Downstream';
    }
}
