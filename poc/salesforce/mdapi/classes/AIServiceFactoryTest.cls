@IsTest
private class AIServiceFactoryTest {

    @IsTest
    static void configFallsBackToStubWhenNoRecordExists() {
        AI_Poc_Config__mdt cfg = AIServiceFactory.config();
        System.assertNotEquals(null, cfg);
        System.assertNotEquals(null, cfg.Context_Named_Credential__c,
            'A named credential must always resolve, even without a config record.');
    }

    @IsTest
    static void overrideWinsOverConfiguration() {
        AIServiceFactory.override_ = new AIContextGraphStub();
        System.assert(AIServiceFactory.contextGraph() instanceof AIContextGraphStub);
    }
}
