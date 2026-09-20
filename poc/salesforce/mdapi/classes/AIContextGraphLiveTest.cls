@IsTest
private class AIContextGraphLiveTest {

    // ------------------------------------------------------------ intent

    @IsTest
    static void readsCreateFieldRequests() {
        AIRequestIntent i = AIRequestIntent.parse(
            'Create a field called Provider NPI on Account');
        System.assertEquals('Create', i.action);
        System.assertEquals('Field', i.targetType);
        System.assertEquals('Provider NPI', i.targetName);
        System.assertEquals('Account', i.targetObject);
    }

    @IsTest
    static void readsUpdateRequestsWithoutANamedTarget() {
        AIRequestIntent i = AIRequestIntent.parse(
            'Update the Account duplicate handling so reactivation is safe');
        System.assertEquals('Update', i.action);
        System.assert(i.terms.contains('ACCOUNT'));
    }

    @IsTest
    static void prefersLongerTypePhrases() {
        System.assertEquals('ValidationRule',
            AIRequestIntent.parse('add a validation rule on Account').targetType,
            '"validation rule" must win over "rule".');
        System.assertEquals('RecordType',
            AIRequestIntent.parse('new record type for Account').targetType);
    }

    @IsTest
    static void dropsNoiseWordsFromTerms() {
        Set<String> t = AISalesforceMetadataSource.extractTerms(
            'Please update the Account field so it does not duplicate');
        System.assert(t.contains('ACCOUNT'));
        System.assert(t.contains('DUPLICATE'));
        System.assert(!t.contains('THE'));
        System.assert(!t.contains('FIELD'), 'Type words must not become search terms.');
    }

    // ------------------------------------------------------------- search

    @IsTest
    static void searchReadsRealMetadataFromThisOrg() {
        AIRequestIntent i = AIRequestIntent.parse('Review the Account object');
        AINetworkServicesScope scope = AINetworkServicesScope.resolve('Network Service');

        Test.startTest();
        AISalesforceMetadataSource.Result r =
            AISalesforceMetadataSource.search(i, scope);
        Test.stopTest();

        System.assert(!r.findings.isEmpty(), 'Account exists in every org.');
        Boolean sawObject = false;
        for (AIContextSlice.Finding f : r.findings) {
            System.assertEquals('Salesforce', f.sourceSystem);
            System.assertNotEquals(null, f.provenance);
            if (f.nodeId == 'sobj:Account') {
                sawObject = true;
                System.assert(f.provenance.contains('describe('),
                    'Provenance must cite the live describe: ' + f.provenance);
            }
        }
        System.assert(sawObject, 'Expected sobj:Account.');
    }

    @IsTest
    static void unmatchedTermsProduceNothingRatherThanAGuess() {
        AIRequestIntent i = AIRequestIntent.parse('Review ZZQQXNOTAREALTHING');
        AISalesforceMetadataSource.Result r = AISalesforceMetadataSource.search(
            i, AINetworkServicesScope.resolve('Network Service'));
        System.assertEquals(0, r.findings.size(),
            'An unmatched term must never produce an invented finding.');
    }

    @IsTest
    static void scopeReportsWhenTheProfileIsMissing() {
        AINetworkServicesScope s = AINetworkServicesScope.resolve('No Such Profile Here');
        System.assertEquals(false, s.profileFound);
        System.assert(s.note.contains('not found'), s.note);
        System.assert(s.covers('Account'),
            'Without a profile the search must fall back to the whole org, not to nothing.');
    }

    // ------------------------------------------------------------ verdict

    @IsTest
    static void creatingSomethingThatExistsIsRefused() {
        AIRequestIntent i = AIRequestIntent.parse(
            'Create a field called Industry on Account');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('field:Account.Industry', 'Field', 'Industry',
                'SOBJECT_HAS_FIELD -> sobj:Account', 'Direct', 'Low', 'Salesforce',
                'SCHEMA Account.Industry · PICKLIST · standard')
        };

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertEquals(AIReuseAnalyzer.ALREADY_EXISTS, v.outcome);
        System.assertEquals(true, v.blocksCreation,
            'A duplicate request must be flagged, not waved through.');
        System.assert(v.headline.contains('Industry'), v.headline);
        System.assert(v.recommendation.contains('Reuse'), v.recommendation);
        System.assertEquals(1, v.evidence.size(),
            'The existing component must be cited as evidence.');
    }

    @IsTest
    static void nameVariantsStillCountAsDuplicates() {
        AIRequestIntent i = AIRequestIntent.parse(
            'Create a field called Provider NPI on Account');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('field:Account.Provider_NPI__c', 'Field',
                'Provider_NPI__c', 'SOBJECT_HAS_FIELD -> sobj:Account',
                'Direct', 'Low', 'Salesforce', 'SCHEMA Account.Provider_NPI__c')
        };
        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);
        System.assertEquals(AIReuseAnalyzer.ALREADY_EXISTS, v.outcome,
            '"Provider NPI" and "Provider_NPI__c" are the same field.');
    }

    @IsTest
    static void creatingSomethingNewIsAllowedAndFlagsNearMisses() {
        AIRequestIntent i = AIRequestIntent.parse(
            'Create a field called Provider NPI Verified on Account');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('field:Account.Provider_NPI__c', 'Field',
                'Provider NPI', 'SOBJECT_HAS_FIELD -> sobj:Account',
                'Direct', 'Low', 'Salesforce', 'SCHEMA Account.Provider_NPI__c'),
            AIContextSlice.build('flow:Acct_Update', 'Flow', 'Account Update',
                'FLOW_UPDATES_SOBJECT -> Account', 'One Hop', 'High', 'Salesforce',
                'METADATA Flow Acct_Update v3')
        };

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertEquals(AIReuseAnalyzer.SAFE_TO_CREATE, v.outcome);
        System.assertEquals(false, v.blocksCreation);
        System.assert(v.detail.contains('similarly named'),
            'A near miss should be surfaced, not hidden: ' + v.detail);
        System.assert(v.recommendation.contains('regression'),
            'Existing automation should raise a coverage note: ' + v.recommendation);
    }

    @IsTest
    static void updateRequestsReportBlastRadius() {
        AIRequestIntent i = AIRequestIntent.parse('Update the Account duplicate logic');
        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build('sobj:Account', 'SObject', 'Account', 'target',
                'Direct', 'High', 'Salesforce', 'SCHEMA describe(Account)'),
            AIContextSlice.build('trigger:AccountTrigger', 'ApexTrigger',
                'AccountTrigger', 'TRIGGER_FIRES_ON_SOBJECT -> sobj:Account',
                'One Hop', 'High', 'Salesforce', 'METADATA ApexTrigger')
        };

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertEquals(AIReuseAnalyzer.IMPACT_ASSESSED, v.outcome);
        System.assert(v.headline.contains('blast radius'), v.headline);
        System.assert(v.recommendation.contains('not the whole org'),
            'The bounded-context point should be explicit: ' + v.recommendation);
    }

    @IsTest
    static void nothingFoundAsksForClarityRatherThanGuessing() {
        AIRequestIntent i = AIRequestIntent.parse('Update the ZZQQX thing');
        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(
            i, new List<AIContextSlice.Finding>());
        System.assertEquals(AIReuseAnalyzer.NEEDS_CLARITY, v.outcome);
        System.assert(v.recommendation.contains('explicitly'), v.recommendation);
    }

    // ------------------------------------------------------------ end to end

    @IsTest
    static void liveQueryRunsEndToEnd() {
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Review the Account object', 'Update Existing', 'Codex');

        Test.startTest();
        AIContextSlice slice = new AIContextGraphLive().query(req);
        Test.stopTest();

        System.assert(slice.snapshotId.startsWith('live-'),
            'Snapshot must mark this as a live read, not a fixture.');
        System.assert(slice.summary.contains('Read:'), slice.summary);
        System.assert(slice.summary.contains('Scope:'), slice.summary);
    }

    @IsTest
    static void factoryChoosesLiveByDefault() {
        AIServiceFactory.graphOverride = null;
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphLive);
    }
}
