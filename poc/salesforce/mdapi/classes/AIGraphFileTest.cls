@IsTest
private class AIGraphFileTest {

    /** Widget -> Cost (field), WidgetTrigger -> Widget, Service -> Widget,
        Test -> Service. The test class is two hops from the object. */
    private static AIGraphDocument sample() {
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'snap1';
        d.addNode('sobj:Widget__c', 'SObject', 'Widget', 'Widget__c',
            '{"fieldCount":12}', 'High', 'SCHEMA describe(Widget__c)', 'Salesforce');
        d.addNode('field:Widget__c.Cost__c', 'Field', 'Cost', 'Cost__c',
            '{"dataType":"CURRENCY"}', 'Low', 'SCHEMA Widget__c.Cost__c', 'Salesforce');
        d.addNode('trigger:WidgetTrigger', 'ApexTrigger', 'WidgetTrigger',
            'WidgetTrigger', '{}', 'High', 'METADATA trigger', 'Salesforce');
        d.addNode('apex:WidgetService', 'ApexClass', 'WidgetService',
            'WidgetService', '{}', 'Medium', 'METADATA class', 'Salesforce');
        d.addNode('apex:WidgetServiceTest', 'TestClass', 'WidgetServiceTest',
            'WidgetServiceTest', '{"test":true}', 'Low', 'METADATA class', 'Salesforce');
        d.addEdge('sobj:Widget__c', 'SOBJECT_HAS_FIELD', 'field:Widget__c.Cost__c', 'describe');
        d.addEdge('trigger:WidgetTrigger', 'TRIGGER_FIRES_ON_SOBJECT', 'sobj:Widget__c', 'TableEnumOrId');
        d.addEdge('apex:WidgetService', 'APEX_REFERENCES_SOBJECT', 'sobj:Widget__c', 'body scan');
        d.addEdge('apex:WidgetServiceTest', 'TEST_COVERS_COMPONENT', 'apex:WidgetService', 'coverage');
        return d;
    }

    @IsTest
    static void fileRoundTripsThroughContentVersion() {
        Test.startTest();
        AIGraphFileStore.save('graph-unit-test', sample());
        Test.stopTest();

        AIGraphDocument back = AIGraphFileStore.load('graph-unit-test');
        System.assertNotEquals(null, back, 'The file must come back.');
        System.assertEquals(5, back.nodes.size());
        System.assertEquals(4, back.relationships.size());
        System.assertEquals('snap1', back.snapshotId);
        System.assertEquals('SObject', back.nodes[0].nodeType,
            'Node type must survive serialization.');
        System.assertNotEquals(null, back.exportedAt,
            'save() must stamp the export time.');
    }

    @IsTest
    static void savingTwiceCreatesAVersionNotASecondFile() {
        AIGraphFileStore.save('graph-unit-test', sample());
        AIGraphFileStore.save('graph-unit-test', sample());

        System.assertEquals(1, [SELECT COUNT() FROM ContentDocument
                                WHERE Title = 'graph-unit-test'],
            'A re-sync must version the file, not litter the org with copies.');
        Map<String, Object> info = AIGraphFileStore.describe('graph-unit-test');
        System.assertEquals(2, info.get('version'));
    }

    @IsTest
    static void oversizedGraphIsRefusedRatherThanTruncated() {
        AIGraphDocument big = new AIGraphDocument();
        big.source = 'SALESFORCE';
        String padding = 'x'.repeat(2000);
        for (Integer i = 0; i < 1400; i++) {
            big.addNode('n:' + i, 'Field', padding, 'f' + i, '{}', 'Low',
                padding, 'Salesforce');
        }
        try {
            AIGraphFileStore.save('graph-unit-oversize', big);
            System.assert(false, 'A graph too large to load must be refused.');
        } catch (AIGraphFileStore.GraphFileException e) {
            System.assert(e.getMessage().contains('ceiling'), e.getMessage());
            System.assert(e.getMessage().contains('Narrow the pod scope'),
                'The error must say what to do: ' + e.getMessage());
        }
    }

    @IsTest
    static void oneHopFindsWhatDirectlyTouchesTheObject() {
        AIGraphMemory g = AIGraphMemory.fromDocument(sample());
        Set<String> reached = new Set<String>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Widget__c'}, 1, 50)) {
            reached.add(h.node.id);
        }
        System.assert(reached.contains('trigger:WidgetTrigger'),
            'Incoming edges matter: a trigger points AT the object it fires on.');
        System.assert(reached.contains('apex:WidgetService'));
        System.assert(!reached.contains('apex:WidgetServiceTest'),
            'The test class is two hops out and must not appear at one.');
    }

    @IsTest
    static void twoHopsReachTheTestCoveringTheCaller() {
        AIGraphMemory g = AIGraphMemory.fromDocument(sample());
        Boolean found = false;
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Widget__c'}, 2, 50)) {
            if (h.node.id == 'apex:WidgetServiceTest') {
                found = true;
                System.assertEquals(2, h.hops);
                System.assert(h.path.contains('TEST_COVERS_COMPONENT'),
                    'The path must name the edge walked: ' + h.path);
            }
        }
        System.assert(found,
            'Reachability at depth is the thing a keyword search cannot do: '
            + 'Widget__c and WidgetServiceTest share no matching name.');
    }

    @IsTest
    static void traversalCostsNoQueriesOnceLoaded() {
        AIGraphMemory g = AIGraphMemory.fromDocument(sample());
        Integer before = Limits.getQueries();
        g.blastRadius(new List<String>{'sobj:Widget__c'}, 3, 50);
        System.assertEquals(before, Limits.getQueries(),
            'In-memory traversal must not query at all.');
    }

    @IsTest
    static void combineMergesSourcesAndDedupes() {
        AIGraphDocument jira = new AIGraphDocument();
        jira.source = 'JIRA';
        jira.addNode('req:NS-1', 'Requirement', 'Stop duplicates', 'NS-1',
            '{}', 'Medium', 'JIRA_ISSUE NS-1', 'Jira');
        jira.addEdge('req:NS-1', 'REQUIREMENT_IMPLEMENTED_BY',
            'apex:WidgetService', 'linked in Jira');

        AIGraphDocument combined = AIGraphDocument.combine(
            new List<AIGraphDocument>{ sample(), jira, sample() });

        System.assertEquals(6, combined.nodes.size(),
            'The duplicate Salesforce document must not double the nodes.');
        System.assertEquals('COMBINED', combined.source);

        AIGraphMemory g = AIGraphMemory.fromDocument(combined);
        Boolean crossed = false;
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Widget__c'}, 3, 50)) {
            if (h.node.sourceSystem == 'Jira') {
                crossed = true;
            }
        }
        System.assert(crossed,
            'Combining sources is the point: a Jira requirement should be '
            + 'reachable from a Salesforce object.');
    }

    @IsTest
    static void contextServiceReportsAnUnbuiltGraph() {
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Review Widget', 'Update Existing', 'Codex');
        AIContextSlice slice = new AIContextGraphFile().query(req);
        System.assertEquals(0, slice.findings.size());
        System.assert(slice.summary.contains('not been exported'),
            'An absent graph must say so: ' + slice.summary);
    }

    @IsTest
    static void scopeGuardRefusesAWholeOrg() {
        // The record build silently walked ~1,400 objects and wrote 221 MB.
        System.assert(AIGraphSalesforceExport.MAX_OBJECTS < 500,
            'The guard must be well below org scale.');
    }

    @IsTest
    static void factoryUsesTheFileBackedGraph() {
        AIServiceFactory.graphOverride = null;
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphFile);
    }
}
