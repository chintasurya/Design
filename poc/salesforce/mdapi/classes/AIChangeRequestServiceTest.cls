@IsTest
private class AIChangeRequestServiceTest {

    private class StubFailureException extends Exception {}

    private class ThrowingGraph implements AIContextGraphService {
        public AIContextSlice query(AI_Change_Request__c request) {
            throw new StubFailureException('service unreachable');
        }
    }

    @IsTest
    static void createRejectsEmptyRequest() {
        try {
            AIChangeRequestService.create('   ');
            System.assert(false, 'Expected a StateException for blank request text.');
        } catch (AIChangeRequestService.StateException e) {
            System.assert(e.getMessage().contains('Describe the change'),
                'Unexpected message: ' + e.getMessage());
        }
    }

    @IsTest
    static void createAssignsCorrelationIdAndDraftStatus() {
        AI_Change_Request__c req = AIChangeRequestService.create('Stop HFN duplicating on reactivation');

        AI_Change_Request__c saved = [
            SELECT Status__c, Correlation_Id__c, Pod__c, Model__c, Request_Type__c
            FROM AI_Change_Request__c WHERE Id = :req.Id];
        System.assertEquals(AIChangeRequestService.DRAFT, saved.Status__c);
        System.assertEquals('Network Services', saved.Pod__c);
        System.assertEquals(null, saved.Model__c,
            'No model is chosen at creation. The request may turn out not to '
            + 'need one, and a picklist default would have looked like a choice '
            + 'somebody made.');
        System.assertEquals('Update Existing', saved.Request_Type__c,
            'Read from the sentence, not asked for.');
        System.assertEquals(36, saved.Correlation_Id__c.length(),
            'Correlation id should be a 36 character uuid-shaped string.');
    }

    @IsTest
    static void theTypeIsReadFromTheSentence() {
        // The person typing does not know whether what they want already
        // exists. That is the question they came here with, so asking them to
        // answer it first was both rude and a way to steer the search wrong.
        System.assertEquals('New Enhancement',
            AIChangeRequestService.derivedType(
                'create a Provider NPI field on Account'));
        System.assertEquals('Update Existing',
            AIChangeRequestService.derivedType(
                'change the HFN expiry logic so it stops duplicating'));
        System.assertEquals('Update Existing',
            AIChangeRequestService.derivedType('the HFN expiry thing'),
            'An unreadable action must not be assumed new: that is the '
            + 'assumption that skips the duplicate check.');
    }

    @IsTest
    static void theModelIsNotChoosableBeforeTheAnalysisIsApproved() {
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Add an HFN expiry warning');
        try {
            AIChangeRequestService.chooseModel(req.Id, 'Claude');
            System.assert(false, 'Expected a StateException at Draft.');
        } catch (AIChangeRequestService.StateException e) {
            System.assert(e.getMessage().contains('analysis is approved'),
                'It must say why, not just refuse: ' + e.getMessage());
        }
    }

    @IsTest
    static void theModelIsChosenAfterTheFirstGate() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Add an HFN expiry warning');

        Test.startTest();
        AIChangeRequestService.analyze(req.Id);
        AIChangeRequestService.approveAnalysis(req.Id);
        AIChangeRequestService.chooseModel(req.Id, 'Gemini');
        Test.stopTest();

        AI_Change_Request__c saved = [
            SELECT Status__c, Model__c FROM AI_Change_Request__c
            WHERE Id = :req.Id];
        System.assertEquals('Gemini', saved.Model__c);
        System.assertEquals(AIChangeRequestService.TICKET_CREATED,
            saved.Status__c,
            'Choosing a model records a decision. It does not advance the '
            + 'state machine, because nothing generates yet.');
    }

    @IsTest
    static void anUnknownModelIsRefused() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create(
            'Add an HFN expiry warning');
        Test.startTest();
        AIChangeRequestService.analyze(req.Id);
        AIChangeRequestService.approveAnalysis(req.Id);
        Test.stopTest();
        try {
            AIChangeRequestService.chooseModel(req.Id, 'Llama');
            System.assert(false, 'Expected a StateException for an unknown model.');
        } catch (AIChangeRequestService.StateException e) {
            System.assert(e.getMessage().contains('Llama'), e.getMessage());
        }
    }

    @IsTest
    static void analyzeStoresFindingsAndParksAtApprovalGate() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create('Update HFN logic');

        Test.startTest();
        AIChangeRequestService.analyze(req.Id);
        Test.stopTest();

        AI_Change_Request__c saved = [
            SELECT Status__c, Snapshot_Id__c, Analysis_Summary__c
            FROM AI_Change_Request__c WHERE Id = :req.Id];
        System.assertEquals(AIChangeRequestService.AWAIT_ANALYSIS, saved.Status__c,
            'Analysis must stop at the first approval gate, not run on.');
        System.assertNotEquals(null, saved.Snapshot_Id__c);

        List<AI_Graph_Finding__c> findings = [
            SELECT Node_Id__c, Source_System__c FROM AI_Graph_Finding__c
            WHERE Change_Request__c = :req.Id];
        System.assertEquals(5, findings.size());

        Set<String> systems = new Set<String>();
        for (AI_Graph_Finding__c f : findings) {
            systems.add(f.Source_System__c);
        }
        System.assertEquals(new Set<String>{'Salesforce', 'Jira', 'Confluence'}, systems,
            'Slice should span all three POC sources.');
    }

    @IsTest
    static void analyzeIsIdempotentAcrossReruns() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create('Update HFN logic');

        AIChangeRequestService.analyze(req.Id);
        // Re-running from the gate should replace findings, never duplicate them.
        req.Status__c = AIChangeRequestService.DRAFT;
        update req;
        AIChangeRequestService.analyze(req.Id);

        System.assertEquals(5, [SELECT COUNT() FROM AI_Graph_Finding__c
                                WHERE Change_Request__c = :req.Id],
            'Re-analysis should replace the previous findings set.');
    }

    @IsTest
    static void analyzeFailureRecordsErrorAndFailsRequest() {
        AIServiceFactory.graphOverride = new ThrowingGraph();
        AI_Change_Request__c req = AIChangeRequestService.create('Update HFN logic');

        try {
            AIChangeRequestService.analyze(req.Id);
            System.assert(false, 'Expected the callout failure to surface.');
        } catch (Exception e) {
            System.assert(e.getMessage().contains('unreachable'));
        }

        AI_Change_Request__c saved = [
            SELECT Status__c, Error_Message__c FROM AI_Change_Request__c
            WHERE Id = :req.Id];
        System.assertEquals(AIChangeRequestService.FAILED, saved.Status__c);
        System.assert(saved.Error_Message__c.contains('unreachable'));
    }

    @IsTest
    static void approvalGatesCannotBeSkipped() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create('Update HFN logic');

        // Straight from Draft to deployment must be refused.
        try {
            AIChangeRequestService.approveCode(req.Id);
            System.assert(false, 'Draft must not be deployable.');
        } catch (AIChangeRequestService.StateException e) {
            System.assert(e.getMessage().contains('Cannot move from'));
        }

        // Approving analysis before analysis has run must also be refused.
        try {
            AIChangeRequestService.approveAnalysis(req.Id);
            System.assert(false, 'Analysis approval requires an analysis.');
        } catch (AIChangeRequestService.StateException e) {
            System.assert(e.getMessage().contains('Cannot move from'));
        }
    }

    @IsTest
    static void happyPathReachesDeployingWithBothApprovalsStamped() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create('Update HFN logic');

        AIChangeRequestService.analyze(req.Id);
        AIChangeRequestService.approveAnalysis(req.Id);

        // Generation is Phase 2; move through it to prove the gate ordering.
        AI_Change_Request__c mid = [SELECT Id, Status__c FROM AI_Change_Request__c
                                    WHERE Id = :req.Id];
        mid.Status__c = AIChangeRequestService.GENERATING;
        update mid;
        mid.Status__c = AIChangeRequestService.AWAIT_CODE;
        update mid;

        AIChangeRequestService.approveCode(req.Id);

        AI_Change_Request__c saved = [
            SELECT Status__c, Analysis_Approved_By__c, Analysis_Approved_At__c,
                   Code_Approved_By__c, Code_Approved_At__c
            FROM AI_Change_Request__c WHERE Id = :req.Id];
        System.assertEquals(AIChangeRequestService.DEPLOYING, saved.Status__c);
        System.assertEquals(UserInfo.getUserId(), saved.Analysis_Approved_By__c);
        System.assertEquals(UserInfo.getUserId(), saved.Code_Approved_By__c);
        System.assertNotEquals(null, saved.Analysis_Approved_At__c);
        System.assertNotEquals(null, saved.Code_Approved_At__c);
    }

    @IsTest
    static void rejectIsAllowedFromAnyGate() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        AI_Change_Request__c req = AIChangeRequestService.create('Update HFN logic');
        AIChangeRequestService.analyze(req.Id);
        AIChangeRequestService.reject(req.Id, 'Business declined the change');

        AI_Change_Request__c saved = [SELECT Status__c, Error_Message__c
                                      FROM AI_Change_Request__c WHERE Id = :req.Id];
        System.assertEquals(AIChangeRequestService.REJECTED, saved.Status__c);
        System.assertEquals('Business declined the change', saved.Error_Message__c);
    }
}
