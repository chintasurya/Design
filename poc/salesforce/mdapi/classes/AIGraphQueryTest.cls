@IsTest
private class AIGraphQueryTest {

    /** A small hand-built graph: object -> field, trigger -> object, apex -> object. */
    private static void seedGraph() {
        insert new List<Graph_Node__c>{
            new Graph_Node__c(Node_Id__c = 'sobj:Widget__c', Node_Type__c = 'SObject',
                Node_Name__c = 'Widget', Api_Name__c = 'Widget__c',
                Source_System__c = 'Salesforce', Risk_Tier__c = 'High',
                Provenance__c = 'SCHEMA describe(Widget__c)', Snapshot_Id__c = 's1'),
            new Graph_Node__c(Node_Id__c = 'field:Widget__c.Cost__c', Node_Type__c = 'Field',
                Node_Name__c = 'Cost', Api_Name__c = 'Cost__c',
                Source_System__c = 'Salesforce', Risk_Tier__c = 'Low',
                Provenance__c = 'SCHEMA Widget__c.Cost__c', Snapshot_Id__c = 's1'),
            new Graph_Node__c(Node_Id__c = 'trigger:WidgetTrigger', Node_Type__c = 'ApexTrigger',
                Node_Name__c = 'WidgetTrigger', Api_Name__c = 'WidgetTrigger',
                Source_System__c = 'Salesforce', Risk_Tier__c = 'High',
                Provenance__c = 'METADATA ApexTrigger', Snapshot_Id__c = 's1'),
            new Graph_Node__c(Node_Id__c = 'apex:WidgetService', Node_Type__c = 'ApexClass',
                Node_Name__c = 'WidgetService', Api_Name__c = 'WidgetService',
                Source_System__c = 'Salesforce', Risk_Tier__c = 'Medium',
                Provenance__c = 'METADATA ApexClass', Snapshot_Id__c = 's1'),
            new Graph_Node__c(Node_Id__c = 'apex:WidgetServiceTest', Node_Type__c = 'TestClass',
                Node_Name__c = 'WidgetServiceTest', Api_Name__c = 'WidgetServiceTest',
                Source_System__c = 'Salesforce', Risk_Tier__c = 'Low',
                Provenance__c = 'METADATA ApexClass', Snapshot_Id__c = 's1')
        };
        insert new List<Graph_Edge__c>{
            new Graph_Edge__c(Edge_Id__c = 'e1', From_Node_Id__c = 'sobj:Widget__c',
                To_Node_Id__c = 'field:Widget__c.Cost__c',
                Edge_Type__c = 'SOBJECT_HAS_FIELD', Origin__c = 'FACTUAL',
                Confidence__c = 1.0, Snapshot_Id__c = 's1'),
            new Graph_Edge__c(Edge_Id__c = 'e2', From_Node_Id__c = 'trigger:WidgetTrigger',
                To_Node_Id__c = 'sobj:Widget__c',
                Edge_Type__c = 'TRIGGER_FIRES_ON_SOBJECT', Origin__c = 'FACTUAL',
                Confidence__c = 1.0, Snapshot_Id__c = 's1'),
            new Graph_Edge__c(Edge_Id__c = 'e3', From_Node_Id__c = 'apex:WidgetService',
                To_Node_Id__c = 'sobj:Widget__c',
                Edge_Type__c = 'APEX_REFERENCES_SOBJECT', Origin__c = 'FACTUAL',
                Confidence__c = 1.0, Snapshot_Id__c = 's1'),
            new Graph_Edge__c(Edge_Id__c = 'e4', From_Node_Id__c = 'apex:WidgetServiceTest',
                To_Node_Id__c = 'apex:WidgetService',
                Edge_Type__c = 'TEST_COVERS_COMPONENT', Origin__c = 'FACTUAL',
                Confidence__c = 1.0, Snapshot_Id__c = 's1')
        };
    }

    @IsTest
    static void oneHopFindsWhatDirectlyTouchesTheObject() {
        seedGraph();
        List<AIGraphQuery.Hit> hits = AIGraphQuery.blastRadius(
            new List<String>{'sobj:Widget__c'}, 1, 50);

        Set<String> reached = new Set<String>();
        for (AIGraphQuery.Hit h : hits) {
            reached.add(h.node.Node_Id__c);
        }
        System.assert(reached.contains('trigger:WidgetTrigger'),
            'Incoming edges matter: a trigger points AT the object it fires on.');
        System.assert(reached.contains('apex:WidgetService'));
        System.assert(reached.contains('field:Widget__c.Cost__c'));
        System.assert(!reached.contains('apex:WidgetServiceTest'),
            'The test class is two hops out and must not appear at one.');
    }

    @IsTest
    static void twoHopsReachTheTestThatCoversTheCaller() {
        seedGraph();
        List<AIGraphQuery.Hit> hits = AIGraphQuery.blastRadius(
            new List<String>{'sobj:Widget__c'}, 2, 50);

        Boolean foundTest = false;
        for (AIGraphQuery.Hit h : hits) {
            if (h.node.Node_Id__c == 'apex:WidgetServiceTest') {
                foundTest = true;
                System.assertEquals(2, h.hops,
                    'Widget -> WidgetService -> WidgetServiceTest is two hops.');
                System.assert(h.path.contains('TEST_COVERS_COMPONENT'),
                    'The path must name the edge it traversed: ' + h.path);
            }
        }
        System.assert(foundTest,
            'This is the query live search cannot answer: reachability at depth.');
    }

    @IsTest
    static void traversalCostIsOneQueryPerHop() {
        seedGraph();
        Integer before = Limits.getQueries();
        AIGraphQuery.blastRadius(new List<String>{'sobj:Widget__c'}, 3, 50);
        Integer used = Limits.getQueries() - before;
        System.assert(used <= 5,
            'Three hops plus the node fetch should cost about four queries, used ' + used);
    }

    @IsTest
    static void seedsPreferTheRequestedType() {
        seedGraph();
        List<Graph_Node__c> seeds = AIGraphQuery.seeds(
            new Set<String>{'WIDGET'}, 'ApexTrigger', 5);
        System.assert(!seeds.isEmpty());
        System.assertEquals('ApexTrigger', seeds[0].Node_Type__c,
            'An explicitly requested type should sort to the front.');
    }

    @IsTest
    static void storedServiceReportsWhenTheGraphIsEmpty() {
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Review Widget', 'Update Existing', 'Codex');
        AIContextSlice slice = new AIContextGraphStored().query(req);
        System.assertEquals(0, slice.findings.size());
        System.assert(slice.summary.contains('not been built'),
            'An empty graph must say so, not silently return nothing: ' + slice.summary);
    }

    @IsTest
    static void storedServiceTraversesAndReportsHops() {
        seedGraph();
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Update the Widget duplicate logic', 'Update Existing', 'Codex');

        AIContextSlice slice = new AIContextGraphStored().query(req);

        System.assert(!slice.findings.isEmpty(), slice.summary);
        System.assert(slice.summary.contains('traversed'), slice.summary);
        System.assert(slice.summary.contains('hop'), slice.summary);
    }

    @IsTest
    static void factoryChoosesTheGraphByDefault() {
        AIServiceFactory.graphOverride = null;
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphStored,
            'The graph is the default now, not live search.');
    }
}
