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
    static void scopeMatchingIgnoresCase() {
        // ObjectPermissions.SobjectType and getGlobalDescribe().keySet() do not
        // reliably agree on casing. A case-sensitive comparison between them
        // produced an empty scope: 350 orphan nodes and zero edges.
        AINetworkServicesScope.clearCache();
        AINetworkServicesScope s =
            AINetworkServicesScope.resolve('System Administrator');
        if (s.profileFound && !s.owned.isEmpty()) {
            String sample = new List<String>(s.owned)[0];
            System.assert(s.covers(sample.toLowerCase()),
                'Lowercase must match: ' + sample);
            System.assert(s.covers(sample.toUpperCase()),
                'Uppercase must match: ' + sample);
        }
    }

    @IsTest
    static void everyNodeIsReachableByAtLeastOneEdge() {
        // An orphan node can never be reached by traversal, so it is noise.
        AIGraphDocument d = sample();
        Set<String> touched = new Set<String>();
        for (AIGraphDocument.GraphEdge e : d.relationships) {
            touched.add(e.fromId);
            touched.add(e.toId);
        }
        for (AIGraphDocument.GraphNode n : d.nodes) {
            System.assert(touched.contains(n.id),
                'Orphan node with no edge: ' + n.id);
        }
    }

    @IsTest
    static void updateDoesNotMatchTheTermDate() {
        // Reported verbatim: asking for a Date field on HealthcareFacility
        // returned six ACC flows, five of which matched only because the word
        // "Update" contains the substring "date".
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.addNode('sobj:HealthcareFacility', 'SObject', 'Healthcare Facility',
            'HealthcareFacility', '{}', 'High', 'SCHEMA', 'Salesforce');
        d.addNode('flow:ACC_Master_Update_a_Case_Flow', 'Flow',
            'ACC Master Update a Case Flow', 'ACC_Master_Update_a_Case_Flow',
            '{}', 'High', 'METADATA', 'Salesforce');
        d.addNode('flow:ACC_Update_Date_On_Chat', 'Flow',
            'ACC Update Date On Chat Transcript', 'ACC_Update_Date_On_Chat',
            '{}', 'High', 'METADATA', 'Salesforce');
        d.addEdge('sobj:HealthcareFacility', 'SOBJECT_HAS_FIELD',
            'sobj:HealthcareFacility', 'self');

        AIGraphMemory g = AIGraphMemory.fromDocument(d);
        Set<String> hits = new Set<String>();
        for (AIGraphDocument.GraphNode n :
                g.seeds(new Set<String>{'DATE'}, null, 10)) {
            hits.add(n.id);
        }

        System.assert(!hits.contains('flow:ACC_Master_Update_a_Case_Flow'),
            '"Update" must not match the term "DATE".');
        System.assert(hits.contains('flow:ACC_Update_Date_On_Chat'),
            'A genuine Date word should still match.');
    }

    @IsTest
    static void camelCaseNamesSplitIntoWords() {
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.addNode('sobj:HealthcareFacility', 'SObject', 'Healthcare Facility',
            'HealthcareFacility', '{}', 'High', 'SCHEMA', 'Salesforce');
        AIGraphMemory g = AIGraphMemory.fromDocument(d);

        System.assertEquals(1, g.seeds(new Set<String>{'FACILITY'}, null, 5).size(),
            'A camel case api name must be searchable by its parts.');
        System.assertEquals(1,
            g.seeds(new Set<String>{'HEALTHCAREFACILITY'}, null, 5).size(),
            'The unbroken form must still match.');
    }

    @IsTest
    static void theNamedObjectAnchorsTheSearch() {
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.addNode('sobj:HealthcareFacility', 'SObject', 'Healthcare Facility',
            'HealthcareFacility', '{}', 'High', 'SCHEMA', 'Salesforce');
        d.addNode('flow:ACC_Update_Something', 'Flow', 'ACC Update Something',
            'ACC_Update_Something', '{}', 'High', 'METADATA', 'Salesforce');
        AIGraphMemory g = AIGraphMemory.fromDocument(d);

        List<AIGraphDocument.GraphNode> anchor =
            g.anchorObject('healthcarefacility');
        System.assertEquals(1, anchor.size(),
            'A lowercase object name must still anchor.');
        System.assertEquals('sobj:HealthcareFacility', anchor[0].id);
        System.assertEquals(0, g.anchorObject('NoSuchObject__c').size());
    }

    @IsTest
    static void loadingReportsTheHeapItActuallyUsed() {
        AIGraphFileStore.save('graph-heap-test', sample());

        Test.startTest();
        AIGraphMemory g = AIGraphMemory.load('graph-heap-test');
        Test.stopTest();

        System.assertNotEquals(null, g);
        System.assert(g.heapLimitBytes > 0,
            'The limit must be captured so the margin is visible.');
        System.assert(g.heapNote().contains('MB heap'), g.heapNote());
    }

    @IsTest
    static void factoryUsesTheFileBackedGraph() {
        AIServiceFactory.graphOverride = null;
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphFile);
    }
}
