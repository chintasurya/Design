/**
 * Resolves which graph implementation to use, from custom metadata, so the
 * switch from stub to live service is a config change rather than a deploy.
 */
public class AIServiceFactory {

    @TestVisible private static AIContextGraphService graphOverride;

    public static AI_Poc_Config__mdt config() {
        AI_Poc_Config__mdt cfg = AI_Poc_Config__mdt.getInstance('Default');
        if (cfg == null) {
            cfg = new AI_Poc_Config__mdt(
                Use_Stub_Graph__c = true,
                Context_Named_Credential__c = 'Semantica_Context_Service',
                Context_Query_Path__c = '/v1/context/query');
        }
        return cfg;
    }

    public static AIContextGraphService contextGraph() {
        if (graphOverride != null) {
            return graphOverride;
        }
        return config().Use_Stub_Graph__c
             ? (AIContextGraphService) new AIContextGraphStub()
             : (AIContextGraphService) new AIContextGraphHttp();
    }
}
