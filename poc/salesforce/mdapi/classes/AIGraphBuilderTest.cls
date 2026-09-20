@IsTest
private class AIGraphBuilderTest {

    @IsTest
    static void buildProducesTypedNodesAndEdges() {
        Test.startTest();
        AIGraphBuilder.run();
        Test.stopTest();

        System.assert(AIGraphQuery.isBuilt(), 'The build must persist nodes.');
        System.assert(AIGraphQuery.edgeCount() > 0, 'The build must persist edges.');

        // The point of a graph is typed relationships, not a flat list.
        Set<String> edgeTypes = new Set<String>();
        for (Graph_Edge__c e : [SELECT Edge_Type__c FROM Graph_Edge__c LIMIT 2000]) {
            edgeTypes.add(e.Edge_Type__c);
        }
        System.assert(edgeTypes.contains('SOBJECT_HAS_FIELD'),
            'Fields must hang off their object. Found: ' + edgeTypes);
    }

    @IsTest
    static void lookupFieldsBecomeObjectToObjectEdges() {
        Test.startTest();
        AIGraphBuilder.run();
        Test.stopTest();

        List<Graph_Edge__c> rels = [
            SELECT From_Node_Id__c, To_Node_Id__c, Provenance__c
            FROM Graph_Edge__c
            WHERE Edge_Type__c = 'SOBJECT_RELATES_TO_SOBJECT' LIMIT 5];
        System.assert(!rels.isEmpty(),
            'A lookup is a real relationship and must become an edge.');
        System.assert(rels[0].Provenance__c.contains('via'),
            'The edge should name the field it came from: ' + rels[0].Provenance__c);
    }

    @IsTest
    static void rebuildUpsertsRatherThanDuplicating() {
        Test.startTest();
        AIGraphBuilder.run();
        Test.stopTest();
        Integer first = AIGraphQuery.nodeCount();

        // Node_Id__c is an external id, so a second pass must not double up.
        AIGraphBuilder second = new AIGraphBuilder();
        second.execute(null, new List<String>{'Account'});

        System.assertEquals(first, AIGraphQuery.nodeCount(),
            'Re-running the build must upsert, never duplicate.');
    }
}
