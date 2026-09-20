@IsTest
private class AIContextGraphLiveTest {

    private class JiraMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"issues":[{"key":"NS-99","fields":{'
                + '"summary":"Account duplicate on reactivation",'
                + '"updated":"2026-09-19T10:00:00.000+0000"}}]}');
            return res;
        }
    }

    private class ForbiddenMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(403);
            res.setBody('{"message":"no licence"}');
            return res;
        }
    }

    @IsTest
    static void extractTermsDropsNoiseWords() {
        Set<String> terms = AISalesforceMetadataSource.extractTerms(
            'Please update the Account logic so that it does not duplicate');
        System.assert(terms.contains('ACCOUNT'), 'Should keep the entity name.');
        System.assert(terms.contains('DUPLICATE'), 'Should keep meaningful words.');
        System.assert(!terms.contains('THE'), 'Should drop stopwords.');
        System.assert(!terms.contains('UPDATE'), 'Should drop verbs that match everything.');
        System.assert(!terms.contains('SO'), 'Should drop tokens under three characters.');
    }

    @IsTest
    static void searchFindsRealObjectsInThisOrg() {
        // Account exists in every org, so this asserts against live metadata
        // rather than a fixture.
        AISalesforceMetadataSource.Result r =
            AISalesforceMetadataSource.search(new Set<String>{'ACCOUNT'});

        System.assert(!r.findings.isEmpty(), 'Account must match something real.');
        Boolean foundSObject = false;
        for (AIContextSlice.Finding f : r.findings) {
            System.assertEquals('Salesforce', f.sourceSystem);
            System.assertNotEquals(null, f.provenance, 'Every finding needs provenance.');
            if (f.nodeId == 'sobj:Account') {
                foundSObject = true;
                System.assert(f.provenance.contains('describe('),
                    'Provenance should name the describe call: ' + f.provenance);
                System.assert(f.provenance.contains('fields'),
                    'Provenance should carry the real field count: ' + f.provenance);
            }
        }
        System.assert(foundSObject, 'Expected sobj:Account among the findings.');
    }

    @IsTest
    static void nonsenseTermsReturnNothingRatherThanInventing() {
        AISalesforceMetadataSource.Result r = AISalesforceMetadataSource.search(
            new Set<String>{'ZZQQXNOTAREALTHING'});
        System.assertEquals(0, r.findings.size(),
            'An unmatched term must produce no findings, never a guess.');
        System.assertNotEquals(null, r.note, 'It should say why it found nothing.');
    }

    @IsTest
    static void liveQueryReportsWhichSourcesRan() {
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Review Account duplicate handling', 'Update Existing', 'Codex');

        Test.startTest();
        AIContextSlice slice = new AIContextGraphLive().query(req);
        Test.stopTest();

        System.assert(slice.summary.contains('Salesforce:'),
            'Summary must report the Salesforce source: ' + slice.summary);
        System.assert(slice.summary.contains('Jira: Jira not configured'),
            'An unconfigured source must say so, not stay silent: ' + slice.summary);
        System.assert(slice.summary.contains('Confluence: Confluence not configured'),
            'Same for Confluence: ' + slice.summary);
        System.assert(slice.snapshotId.startsWith('live-'),
            'Snapshot id should mark this as a live read, not a stub.');
    }

    @IsTest
    static void jiraFindingsCarryTheIssueKey() {
        Test.setMock(HttpCalloutMock.class, new JiraMock());
        Test.startTest();
        AIAtlassianSource.Result r = AIAtlassianSource.searchJira(
            'Jira_Cloud', 'NS', new Set<String>{'ACCOUNT'});
        Test.stopTest();

        System.assertEquals(1, r.findings.size());
        System.assertEquals('req:NS-99', r.findings[0].nodeId);
        System.assertEquals('Jira', r.findings[0].sourceSystem);
        System.assert(r.findings[0].provenance.contains('NS-99'));
    }

    @IsTest
    static void confluenceForbiddenExplainsTheLicenceProblem() {
        Test.setMock(HttpCalloutMock.class, new ForbiddenMock());
        Test.startTest();
        AIAtlassianSource.Result r = AIAtlassianSource.searchConfluence(
            'Confluence_Cloud', 'NSDOCS', new Set<String>{'ACCOUNT'});
        Test.stopTest();

        System.assertEquals(0, r.findings.size());
        System.assert(r.note.contains('403'), r.note);
        System.assert(r.note.contains('licence'),
            'A 403 should point at the most common cause: ' + r.note);
    }

    @IsTest
    static void factoryChoosesLiveByDefault() {
        AIServiceFactory.graphOverride = null;
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphLive,
            'With the stub off and no remote credential, the live source must win.');
    }
}
