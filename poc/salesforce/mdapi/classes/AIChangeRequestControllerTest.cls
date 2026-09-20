@IsTest
private class AIChangeRequestControllerTest {

    @IsTest
    static void consoleViewCarriesRequestAndFindings() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();

        Id reqId = AIChangeRequestController.createRequest(
            'Update HFN logic so reactivation does not duplicate',
            'Update Existing', 'Codex');

        Test.startTest();
        AIChangeRequestController.ConsoleView view =
            AIChangeRequestController.runAnalysis(reqId);
        Test.stopTest();

        System.assertEquals(AIChangeRequestService.AWAIT_ANALYSIS,
            view.request.Status__c);
        System.assertEquals(5, view.findings.size());
        System.assertEquals(0, view.artifacts.size());
        System.assertEquals(0, view.testResults.size());
    }

    @IsTest
    static void controllerSurfacesStateErrorsToTheUi() {
        Id reqId = AIChangeRequestController.createRequest(
            'Update HFN logic', 'Update Existing', 'Codex');
        try {
            AIChangeRequestController.approveCode(reqId);
            System.assert(false, 'Expected an AuraHandledException.');
        } catch (AuraHandledException e) {
            System.assert(true);
        }
    }

    @IsTest
    static void approveAndRejectRoundTripThroughController() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        Id reqId = AIChangeRequestController.createRequest(
            'Add HFN expiry warning', 'New Enhancement', 'Gemini');

        AIChangeRequestController.runAnalysis(reqId);
        AIChangeRequestController.ConsoleView approved =
            AIChangeRequestController.approveAnalysis(reqId);
        System.assertEquals(AIChangeRequestService.TICKET_CREATED,
            approved.request.Status__c);

        AIChangeRequestController.ConsoleView rejected =
            AIChangeRequestController.rejectRequest(reqId, 'Superseded');
        System.assertEquals(AIChangeRequestService.REJECTED,
            rejected.request.Status__c);
    }
}
