@IsTest
private class AIChangeRequestControllerTest {

    @IsTest
    static void consoleViewCarriesRequestAndFindings() {
        AIServiceFactory.graphOverride = new AIContextGraphStub();

        Id reqId = AIChangeRequestController.createRequest('Update HFN logic so reactivation does not duplicate');

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
        Id reqId = AIChangeRequestController.createRequest('Update HFN logic');
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
        Id reqId = AIChangeRequestController.createRequest('Add HFN expiry warning');

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

    @IsTest
    static void theModelQuestionIsAskedAfterTheGate() {
        // The three model buttons used to sit on the entry screen, next to the
        // text box, before anything had been searched. They belong here: after
        // the evidence is in and a human has accepted it.
        AIServiceFactory.graphOverride = new AIContextGraphStub();
        Id reqId = AIChangeRequestController.createRequest(
            'Add HFN expiry warning');

        AIChangeRequestController.runAnalysis(reqId);
        AIChangeRequestController.ConsoleView beforeChoice =
            AIChangeRequestController.getView(reqId);
        System.assertEquals(null, beforeChoice.request.Model__c,
            'No model until the analysis is approved.');

        AIChangeRequestController.approveAnalysis(reqId);
        AIChangeRequestController.ConsoleView chosen =
            AIChangeRequestController.chooseModel(reqId, 'Claude');

        System.assertEquals('Claude', chosen.request.Model__c);
        System.assertEquals(AIChangeRequestService.TICKET_CREATED,
            chosen.request.Status__c);
    }
}
