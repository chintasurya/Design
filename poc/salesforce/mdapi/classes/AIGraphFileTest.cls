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
        AI_Change_Request__c req = AIChangeRequestService.create('Review Widget');
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
    static void behaviourRequestsAreReadAsBehaviour() {
        AIRequestIntent i = AIRequestIntent.parse(
            'when Account record gets created i want to create '
            + 'HealthcareProvider and HealthcareFacility record');

        System.assertEquals('Behaviour', i.requestShape,
            'A trigger clause makes this a behaviour, not a component request.');
        System.assertEquals('Account', i.triggerObject);
        System.assertEquals('Created', i.triggerEvent);
        System.assert(i.affectedObjects.contains('HealthcareProvider'),
            'Objects written by the behaviour must be captured: '
            + i.affectedObjects);
        System.assert(i.affectedObjects.contains('HealthcareFacility'));
        System.assertEquals(null, i.targetName,
            'A behaviour has no single component name to duplicate-check.');
    }

    @IsTest
    static void existingAutomationBlocksAFalseClearance() {
        // Reported verbatim: this returned Safe to Create while a Flow on
        // Account already created both records.
        AIRequestIntent i = AIRequestIntent.parse(
            'when Account record gets created i want to create '
            + 'HealthcareProvider and HealthcareFacility record');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('flow:Acct_Create_Provider', 'Flow',
                'Account Create Provider', 'FLOW_UPDATES_SOBJECT -> sobj:Account',
                'One Hop', 'High', 'Salesforce', 'METADATA Flow v3')
        };

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertNotEquals(AIReuseAnalyzer.SAFE_TO_CREATE, v.outcome,
            'Automation exists on the trigger object, so this can never be '
            + 'cleared as safe.');
        System.assertEquals(true, v.blocksCreation);
        System.assert(v.detail.contains('Tooling API'),
            'It must say why it cannot be certain: ' + v.detail);
    }

    @IsTest
    static void automationNamingTheTargetIsFlaggedHarder() {
        AIRequestIntent i = AIRequestIntent.parse(
            'when Account record gets created i want to create '
            + 'HealthcareProvider record');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('flow:Create_HealthcareProvider', 'Flow',
                'Create HealthcareProvider on Account',
                'FLOW_UPDATES_SOBJECT -> sobj:Account', 'One Hop', 'High',
                'Salesforce', 'METADATA Flow v2')
        };

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertEquals(AIReuseAnalyzer.LIKELY_HANDLED, v.outcome,
            'Automation naming the target object is the strongest signal '
            + 'the behaviour already exists.');
        System.assert(v.detail.contains('duplicate records'), v.detail);
    }

    @IsTest
    static void noAutomationStillClears() {
        // The clearance is legitimate only because the trigger object is in
        // the evidence: the graph held Widget__c, searched it, and found no
        // automation. That is the difference between a searched absence and
        // an unsearched one.
        AIRequestIntent i = AIRequestIntent.parse(
            'when Widget__c record gets created i want to create Gadget__c record');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('sobj:Widget__c', 'SObject', 'Widget',
                'Matched the request directly', 'Direct', 'Medium', 'Salesforce',
                'SCHEMA describe(Widget__c)')
        };
        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);
        System.assertEquals(AIReuseAnalyzer.SAFE_TO_CREATE, v.outcome,
            'With nothing firing on the object there is nothing to duplicate.');
    }

    @IsTest
    static void anUnsearchedObjectIsNeverCleared() {
        // The reported bug, reduced to its root: the graph did not hold
        // Account, so it found no automation on Account, so it said the
        // behaviour was safe to build. Nothing had been searched. An absence
        // of evidence was being reported as evidence of absence.
        AIRequestIntent i = AIRequestIntent.parse(
            'when Account record gets created i want to create '
            + 'HealthcareProvider record');

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(
            i, new List<AIContextSlice.Finding>());

        System.assertNotEquals(AIReuseAnalyzer.SAFE_TO_CREATE, v.outcome,
            'Nothing was searched, so nothing can be cleared.');
        System.assertEquals(true, v.blocksCreation);
        System.assert(v.headline.contains('Account'),
            'It must name the object it could not see: ' + v.headline);
    }

    @IsTest
    static void automationIsNotCrowdedOutByFields() {
        // Why the Flow on Account stayed invisible even once it was in the
        // graph. Account carries hundreds of fields, each one a structural
        // edge, and the node budget was spent on columns before the traversal
        // ever reached the automation pointing at the object.
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'crowding';
        d.addNode('sobj:Account', 'SObject', 'Account', 'Account',
            '{"fieldCount":120}', 'High', 'SCHEMA describe(Account)', 'Salesforce');
        for (Integer n = 0; n < 120; n++) {
            String fieldId = 'field:Account.F' + n + '__c';
            d.addNode(fieldId, 'Field', 'F' + n, 'F' + n + '__c',
                '{"dataType":"STRING"}', 'Low', 'SCHEMA field', 'Salesforce');
            d.addEdge('sobj:Account', 'SOBJECT_HAS_FIELD', fieldId, 'describe');
        }
        d.addNode('flow:Create_Provider_On_Account', 'Flow',
            'Create Provider On Account', 'Create_Provider_On_Account',
            '{"processType":"AutoLaunchedFlow"}', 'High',
            'METADATA Flow v3', 'Salesforce');
        d.addEdge('flow:Create_Provider_On_Account', 'FLOW_UPDATES_SOBJECT',
            'sobj:Account', 'record-triggered on Account');

        AIGraphMemory g = AIGraphMemory.fromDocument(d);

        Set<String> reached = new Set<String>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Account'}, 1, 20)) {
            reached.add(h.node.id);
        }
        System.assert(reached.contains('flow:Create_Provider_On_Account'),
            'Behaviour must be walked before structure, or 120 columns bury '
            + 'the one Flow that answers the question. Reached: ' + reached);

        Set<String> behaviourOnly = new Set<String>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Account'}, 1, 20,
                new Set<String>{'Field', 'RecordType'})) {
            behaviourOnly.add(h.node.id);
        }
        System.assertEquals(2, behaviourOnly.size(),
            'Excluded types must not reach the result at all: ' + behaviourOnly);
        System.assert(behaviourOnly.contains('flow:Create_Provider_On_Account'));
    }

    @IsTest
    static void boundaryObjectsKeepAutomationReachable() {
        // A Flow record-triggered on an object outside the pod used to be
        // dropped whole, because its target could not be resolved inside the
        // scope. The object now enters as a boundary node: one node, no
        // fields, enough for the Flow to hang off and be found.
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'boundary';
        d.addNode('sobj:Account', 'SObject', 'Account', 'Account',
            '{"boundary":true}', 'Medium',
            'SCHEMA Account · outside the pod scope, included because '
            + 'automation in scope fires on it', 'Salesforce');
        d.addNode('flow:Acct_Create_Provider', 'Flow', 'Acct Create Provider',
            'Acct_Create_Provider', '{}', 'High', 'METADATA Flow v1', 'Salesforce');
        d.addEdge('flow:Acct_Create_Provider', 'FLOW_UPDATES_SOBJECT',
            'sobj:Account', 'record-triggered on Account');

        AIGraphMemory g = AIGraphMemory.fromDocument(d);
        System.assertEquals(1, g.anchorObject('Account').size(),
            'A boundary node must still anchor a search.');

        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Account'}, 1, 20)) {
            findings.add(AIContextSlice.build(h.node.id, h.node.nodeType,
                h.node.name, h.path, h.hops == 0 ? 'Direct' : 'One Hop',
                h.node.riskTier, h.node.sourceSystem, h.node.provenance));
        }

        AIRequestIntent i = AIRequestIntent.parse(
            'when Account record gets created i want to create '
            + 'HealthcareProvider record');
        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertNotEquals(AIReuseAnalyzer.SAFE_TO_CREATE, v.outcome,
            'The Flow on Account is now visible, so this can never clear.');
        System.assertEquals(true, v.blocksCreation);
    }

    @IsTest
    static void theDeclaredPodIsTheAuthorityNotTheProfile() {
        // Several pod objects are created by automation, never by people, so
        // the pod profile has no create permission on them. Deriving scope
        // from create access is what hid HealthcareFacilityNetwork, which is
        // the object most questions are actually about.
        Set<String> declared = new Set<String>(AINetworkServicesPod.OBJECTS);
        for (String automated : AINetworkServicesPod.CREATED_BY_AUTOMATION) {
            System.assert(declared.contains(automated),
                automated + ' is created by automation and must still be '
                + 'declared, or it never reaches the graph: ' + declared);
        }
    }

    @IsTest
    static void podNamingRecognisesTheConventionsInUse() {
        System.assert(AINetworkServicesPod.namedForPod('AHC_AccountTrigger'));
        System.assert(AINetworkServicesPod.namedForPod('AHC_LeadTriggerHandler'));
        System.assert(AINetworkServicesPod.namedForPod('NS_HFN_Generation'));
        System.assert(AINetworkServicesPod.namedForPod(
            'Network Services HFN Generation'));
        System.assert(!AINetworkServicesPod.namedForPod('AccountTriggerHandler'),
            'A class with no pod prefix is not the pod\'s by name. It can '
            + 'still enter the graph by being called, which is the point of '
            + 'the call edges.');

        System.assert(AINetworkServicesPod.podRecordType('Network_Services'));
        System.assert(AINetworkServicesPod.podRecordType('Network_Services_TX_CIN'));
        System.assert(!AINetworkServicesPod.podRecordType('Network_Partner'),
            'Matching the bare word "network" would have caught this.');
    }

    @IsTest
    static void aHandlersHandlerIsReachableFromTheObject() {
        // "How is an HFN generated" is answered by walking from the object to
        // the trigger, to its handler, to the class the handler delegates to.
        // Without call edges the chain stops at the trigger and the answer is
        // the name of a file that contains two lines.
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'chain';
        d.addNode('sobj:Account', 'SObject', 'Account', 'Account',
            '{}', 'High', 'SCHEMA describe(Account)', 'Salesforce');
        d.addNode('trigger:AHC_AccountTrigger', 'ApexTrigger',
            'AHC_AccountTrigger', 'AHC_AccountTrigger', '{"pod":true}', 'High',
            'METADATA ApexTrigger on Account', 'Salesforce');
        d.addNode('apex:AHC_AccountTriggerHandler', 'ApexClass',
            'AHC_AccountTriggerHandler', 'AHC_AccountTriggerHandler',
            '{"pod":true}', 'High', 'METADATA ApexClass', 'Salesforce');
        d.addNode('apex:HFNGenerationService', 'ApexClass',
            'HFNGenerationService', 'HFNGenerationService', '{"pod":false}',
            'High', 'METADATA ApexClass', 'Salesforce');
        d.addEdge('trigger:AHC_AccountTrigger', 'TRIGGER_FIRES_ON_SOBJECT',
            'sobj:Account', 'TableEnumOrId');
        d.addEdge('trigger:AHC_AccountTrigger', 'TRIGGER_CALLS_APEX',
            'apex:AHC_AccountTriggerHandler', 'class name in body');
        d.addEdge('apex:AHC_AccountTriggerHandler', 'APEX_CALLS_APEX',
            'apex:HFNGenerationService', 'class name in body');

        AIGraphMemory g = AIGraphMemory.fromDocument(d);
        Map<String, Integer> hopOf = new Map<String, Integer>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Account'}, 3, 50)) {
            hopOf.put(h.node.id, h.hops);
        }
        System.assertEquals(1, hopOf.get('trigger:AHC_AccountTrigger'));
        System.assertEquals(2, hopOf.get('apex:AHC_AccountTriggerHandler'),
            'The handler is two hops from the object, through the trigger.');
        System.assertEquals(3, hopOf.get('apex:HFNGenerationService'),
            'The class that does the work is three hops out, and it shares no '
            + 'name with the object. A keyword search cannot reach it.');
    }

    @IsTest
    static void callEdgesAreWalkedBeforeColumns() {
        // The same crowding problem as fields, now that a class can carry many
        // call edges: behaviour has to be walked first or the budget is spent
        // before the chain is followed.
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'ordering';
        d.addNode('sobj:Account', 'SObject', 'Account', 'Account', '{}', 'High',
            'SCHEMA', 'Salesforce');
        for (Integer n = 0; n < 80; n++) {
            d.addNode('field:Account.F' + n, 'Field', 'F' + n, 'F' + n,
                '{}', 'Low', 'SCHEMA field', 'Salesforce');
            d.addEdge('sobj:Account', 'SOBJECT_HAS_FIELD',
                'field:Account.F' + n, 'describe');
        }
        d.addNode('trigger:AHC_AccountTrigger', 'ApexTrigger',
            'AHC_AccountTrigger', 'AHC_AccountTrigger', '{}', 'High',
            'METADATA', 'Salesforce');
        d.addEdge('trigger:AHC_AccountTrigger', 'TRIGGER_FIRES_ON_SOBJECT',
            'sobj:Account', 'TableEnumOrId');

        AIGraphMemory g = AIGraphMemory.fromDocument(d);
        Set<String> reached = new Set<String>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:Account'}, 1, 10)) {
            reached.add(h.node.id);
        }
        System.assert(reached.contains('trigger:AHC_AccountTrigger'),
            'Eighty columns must not bury the trigger: ' + reached);
    }

    @IsTest
    static void aSecondObjectIsADestinationNotACorridor() {
        // Reported verbatim: "terminate HealthcareFacilityNetwork when due
        // date is exceeded" returned 55 components, every one of them reached
        // via "-> sobj:account". The walk passed THROUGH Account, which
        // carries seventy Apex references, and fanned out across all of them.
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'hub';
        d.addNode('sobj:HealthcareFacilityNetwork', 'SObject',
            'Healthcare Facility Network', 'HealthcareFacilityNetwork',
            '{}', 'High', 'SCHEMA', 'Salesforce');
        d.addNode('sobj:Account', 'SObject', 'Account', 'Account', '{}',
            'High', 'SCHEMA', 'Salesforce');
        d.addNode('apex:HFNTerminationService', 'ApexClass',
            'HFNTerminationService', 'HFNTerminationService', '{}', 'High',
            'METADATA', 'Salesforce');
        d.addEdge('apex:HFNTerminationService', 'APEX_REFERENCES_SOBJECT',
            'sobj:HealthcareFacilityNetwork', 'body');
        d.addEdge('apex:HFNTerminationService', 'APEX_REFERENCES_SOBJECT',
            'sobj:Account', 'body');
        // Account's other seventy callers, which must not arrive.
        for (Integer n = 0; n < 70; n++) {
            d.addNode('apex:Unrelated' + n, 'ApexClass', 'Unrelated' + n,
                'Unrelated' + n, '{}', 'Medium', 'METADATA', 'Salesforce');
            d.addEdge('apex:Unrelated' + n, 'APEX_REFERENCES_SOBJECT',
                'sobj:Account', 'body');
        }

        AIGraphMemory g = AIGraphMemory.fromDocument(d);
        Set<String> reached = new Set<String>();
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:HealthcareFacilityNetwork'}, 3, 60)) {
            reached.add(h.node.id);
        }

        System.assert(reached.contains('apex:HFNTerminationService'),
            'The class that touches the object is the answer.');
        System.assert(reached.contains('sobj:Account'),
            'That Account is involved is worth reporting.');
        System.assertEquals(0, countUnrelated(reached),
            'Account is a destination, not a corridor. Nothing reached only '
            + 'by passing through it belongs in the answer: ' + reached.size()
            + ' nodes came back.');
    }

    private static Integer countUnrelated(Set<String> reached) {
        Integer n = 0;
        for (String id : reached) {
            if (id.startsWith('apex:Unrelated')) {
                n++;
            }
        }
        return n;
    }

    @IsTest
    static void theObjectIsFoundEvenInPhrasingsNobodyTaughtTheParser() {
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'naming';
        d.addNode('sobj:HealthcareFacilityNetwork', 'SObject',
            'Healthcare Facility Network', 'HealthcareFacilityNetwork',
            '{}', 'High', 'SCHEMA', 'Salesforce');
        d.addNode('sobj:Widget__c', 'SObject', 'Widget', 'Widget__c', '{}',
            'Low', 'SCHEMA', 'Salesforce');
        AIGraphMemory g = AIGraphMemory.fromDocument(d);

        // The phrasing that returned nothing: no "on", no "for", no "in".
        List<AIGraphDocument.GraphNode> hit = g.objectsNamedIn(
            'terminate HealthcareFacilityNetwork when due date is exceeded');
        System.assertEquals(1, hit.size(), 'Expected one object, got ' + hit);
        System.assertEquals('sobj:HealthcareFacilityNetwork', hit[0].id);

        System.assertEquals(1,
            g.objectsNamedIn('close the Healthcare Facility Network').size(),
            'The label spelled with spaces is the same object.');
        System.assertEquals(1, g.objectsNamedIn('add a field to Widget').size(),
            'A custom object is found without its __c suffix.');
        System.assertEquals(0,
            g.objectsNamedIn('make the due date required').size(),
            'No object named means no anchor, not a guess.');
    }

    @IsTest
    static void relationshipsReadAsSentencesNotEdgeTypes() {
        // The same row is read by whoever asked for the change and by whoever
        // will build it. "apex:X -[APEX_REFERENCES_SOBJECT]-> sobj:account"
        // serves neither of them.
        AIGraphDocument d = new AIGraphDocument();
        d.source = 'SALESFORCE';
        d.snapshotId = 'readable';
        d.addNode('sobj:HealthcareFacilityNetwork', 'SObject',
            'Healthcare Facility Network', 'HealthcareFacilityNetwork', '{}',
            'High', 'SCHEMA', 'Salesforce');
        d.addNode('flow:NS_HFN_Terminate', 'Flow', 'NS HFN Terminate',
            'NS_HFN_Terminate', '{}', 'High', 'METADATA', 'Salesforce');
        d.addEdge('flow:NS_HFN_Terminate', 'FLOW_UPDATES_SOBJECT',
            'sobj:HealthcareFacilityNetwork', 'record-triggered');

        AIGraphMemory g = AIGraphMemory.fromDocument(d);
        for (AIGraphMemory.Hit h : g.blastRadius(
                new List<String>{'sobj:HealthcareFacilityNetwork'}, 1, 20)) {
            if (h.node.id == 'flow:NS_HFN_Terminate') {
                System.assert(!h.path.contains('FLOW_UPDATES_SOBJECT'),
                    'No edge type names in a row people read: ' + h.path);
                System.assert(h.path.contains('Healthcare Facility Network'),
                    'It must say which object: ' + h.path);
            }
        }
    }

    @IsTest
    static void terminateIsAChangeNotAnUnknownAction() {
        System.assertEquals('Update', AIRequestIntent.parse(
            'terminate HealthcareFacilityNetwork when due date is exceeded')
            .action, 'An unrecognised verb falls back to Analyze, which is '
            + 'the widest possible search.');
        System.assertEquals('Update',
            AIRequestIntent.parse('deactivate the provider record').action);
        System.assertEquals('Create',
            AIRequestIntent.parse('generate an HFN for each facility').action);
    }

    @IsTest
    static void factoryUsesTheFileBackedGraph() {
        AIServiceFactory.graphOverride = null;
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphFile);
    }
}
