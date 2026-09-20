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

        AIGraphMemory graph = AIGraphMemory.load(AIGraphFileStore.COMBINED);
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
        for (AIGraphMemory.Hit h : graph.blastRadius(seedIds, hops, MAX_NODES)) {
            slice.findings.add(AIContextSlice.build(
                h.node.id, h.node.nodeType, h.node.name, h.path,
                impactOf(h.hops), h.node.riskTier, h.node.sourceSystem,
                h.node.provenance));
        }

        slice.summary = 'Read: ' + intent.summary
            + ' · traversed ' + hops + ' hop' + (hops == 1 ? '' : 's')
            + ' from ' + seedBasis
            + ' across ' + graph.nodeCount + ' nodes and ' + graph.edgeCount
            + ' edges · ' + slice.findings.size() + ' reached';
        return slice;
    }

    private static String impactOf(Integer hops) {
        if (hops == 0) { return 'Direct'; }
        if (hops == 1) { return 'One Hop'; }
        if (hops == 2) { return 'Two Hop'; }
        return 'Downstream';
    }
}
