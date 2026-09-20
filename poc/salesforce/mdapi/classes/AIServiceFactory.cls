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
                Use_Stub_Graph__c = false,
                Use_Remote_Graph__c = false,
                Pod_Profile_Name__c = 'Network Service',
                Context_Named_Credential__c = 'Semantica_Context_Service',
                Context_Query_Path__c = '/v1/context/query');
        }
        return cfg;
    }

    public static AIContextGraphService contextGraph() {
        if (graphOverride != null) {
            return graphOverride;
        }
        AI_Poc_Config__mdt cfg = config();
        if (cfg.Use_Stub_Graph__c) {
            // Offline demo only. Returns fixtures, not org data.
            return new AIContextGraphStub();
        }
        if (cfg.Use_Remote_Graph__c
                && String.isNotBlank(cfg.Context_Named_Credential__c)) {
            // Semantica on GCP, once it exists.
            return new AIContextGraphHttp();
        }
        // Default: search this org live, plus Jira and Confluence if configured.
        return new AIContextGraphLive();
    }
}
