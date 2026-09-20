/**
 * Context slices built by traversing the persisted graph.
 *
 * The distinction from the search this replaces: nothing here asks the org a
 * question. It walks edges that were already resolved when the graph was
 * built, which is why it can answer at three hops and report the path a
 * component was reached by.
 */
public with sharing class AIContextGraphStored implements AIContextGraphService {

    private static final Integer MAX_SEEDS = 6;
    private static final Integer MAX_NODES = 60;

    public AIContextSlice query(AI_Change_Request__c request) {
        AIContextSlice slice = new AIContextSlice();
        AIRequestIntent intent = AIRequestIntent.parse(request.Request_Text__c);

        if (!AIGraphQuery.isBuilt()) {
            slice.snapshotId = 'none';
            slice.summary = 'The knowledge graph has not been built yet. '
                + 'Run Build Graph, then ask again.';
            return slice;
        }

        Integer hops = intent.action == 'Create' ? 1 : 3;
        Set<String> terms = new Set<String>(intent.terms);
        if (String.isNotBlank(intent.targetObject)) {
            terms.add(intent.targetObject.toUpperCase());
        }
        if (String.isNotBlank(intent.targetName)) {
            terms.addAll(AISalesforceMetadataSource.extractTerms(intent.targetName));
        }

        List<Graph_Node__c> seeds = AIGraphQuery.seeds(
            terms, intent.targetType, MAX_SEEDS);
        if (seeds.isEmpty()) {
            slice.snapshotId = snapshot();
            slice.summary = 'Read: ' + intent.summary
                + ' · nothing in the graph matched those terms';
            return slice;
        }

        List<String> seedIds = new List<String>();
        for (Graph_Node__c n : seeds) {
            seedIds.add(n.Node_Id__c);
        }

        List<AIGraphQuery.Hit> hits =
            AIGraphQuery.blastRadius(seedIds, hops, MAX_NODES);

        for (AIGraphQuery.Hit h : hits) {
            slice.findings.add(AIContextSlice.build(
                h.node.Node_Id__c,
                h.node.Node_Type__c,
                h.node.Node_Name__c,
                h.path,
                impactOf(h.hops),
                h.node.Risk_Tier__c,
                h.node.Source_System__c,
                h.node.Provenance__c));
        }

        slice.snapshotId = snapshot();
        slice.summary = 'Read: ' + intent.summary
            + ' · traversed ' + hops + ' hop' + (hops == 1 ? '' : 's')
            + ' from ' + seeds.size() + ' seed node'
            + (seeds.size() == 1 ? '' : 's')
            + ' · ' + hits.size() + ' components reached';
        return slice;
    }

    private static String impactOf(Integer hops) {
        if (hops == 0) {
            return 'Direct';
        }
        if (hops == 1) {
            return 'One Hop';
        }
        if (hops == 2) {
            return 'Two Hop';
        }
        return 'Downstream';
    }

    private static String snapshot() {
        List<Graph_Node__c> any = [
            SELECT Snapshot_Id__c FROM Graph_Node__c
            ORDER BY LastModifiedDate DESC LIMIT 1];
        return any.isEmpty() ? 'none' : any[0].Snapshot_Id__c;
    }
}
