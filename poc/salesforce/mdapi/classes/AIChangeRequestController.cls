/**
 * LWC entry points for the AI change console.
 *
 * Thin by design: every method delegates to AIChangeRequestService so the
 * state rules live in one place and stay testable without a UI.
 */
public with sharing class AIChangeRequestController {

    public class ConsoleView {
        @AuraEnabled public AI_Change_Request__c request;
        @AuraEnabled public List<AI_Graph_Finding__c> findings;
        @AuraEnabled public List<AI_Generated_Artifact__c> artifacts;
        @AuraEnabled public List<AI_Test_Result__c> testResults;
        @AuraEnabled public AIReuseAnalyzer.Verdict verdict;
    }

    /** Step 1. What is being asked for. Returned so the user can correct a misread. */
    @AuraEnabled
    public static AIContextGraphLive.Step stepUnderstand(Id requestId) {
        Long t0 = System.currentTimeMillis();
        try {
            AI_Change_Request__c req = [
                SELECT Id, Request_Text__c FROM AI_Change_Request__c
                WHERE Id = :requestId WITH USER_MODE LIMIT 1];
            AIRequestIntent intent = AIRequestIntent.parse(req.Request_Text__c);
            return new AIContextGraphLive.Step('understand', 'Understood the request',
                intent.summary, elapsed(t0));
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    /** Step 2. Which objects the pod's profile can actually see. */
    @AuraEnabled
    public static AIContextGraphLive.Step stepScope(Id requestId) {
        Long t0 = System.currentTimeMillis();
        try {
            AINetworkServicesScope scope = AINetworkServicesScope.resolve(
                AIServiceFactory.config().Pod_Profile_Name__c);
            String detail = scope.note;
            return new AIContextGraphLive.Step('scope',
                'Resolved the Network Services scope', detail, elapsed(t0));
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    /** Step 3. The live metadata search. Writes the findings rows. */
    @AuraEnabled
    public static AIContextGraphLive.Step stepSearch(Id requestId) {
        Long t0 = System.currentTimeMillis();
        try {
            AIChangeRequestService.analyze(requestId);
            Integer n = [SELECT COUNT() FROM AI_Graph_Finding__c
                         WHERE Change_Request__c = :requestId];
            return new AIContextGraphLive.Step('search', 'Searched live org metadata',
                n == 0 ? 'Nothing matched in scope'
                       : n + ' connected components identified', elapsed(t0));
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    /** Step 4. Reuse or create, and what that means. */
    @AuraEnabled
    public static ConsoleView stepAssess(Id requestId) {
        try {
            return getView(requestId);
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    /** Export the Salesforce graph to its JSON file, then re-merge the combined file. */
    @AuraEnabled
    public static String buildGraph() {
        try {
            return String.valueOf(AIGraphSalesforceExport.start());
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    /** Profiles in the org, so the pod profile can be picked rather than guessed. */
    @AuraEnabled(cacheable=false)
    public static List<Map<String, Object>> listProfiles() {
        try {
            return AINetworkServicesScope.candidates();
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    @AuraEnabled(cacheable=false)
    public static Map<String, Object> graphStatus() {
        try {
            Map<String, Object> file =
                AIGraphFileStore.describe(AIGraphFileStore.COMBINED);
            Boolean built = (Boolean) file.get('exists');
            List<AsyncApexJob> jobs = [
                SELECT Status, JobItemsProcessed, TotalJobItems, NumberOfErrors,
                       ExtendedStatus
                FROM AsyncApexJob
                WHERE ApexClass.Name = 'AIGraphSalesforceExport'
                ORDER BY CreatedDate DESC LIMIT 1];
            AINetworkServicesScope scope = AINetworkServicesScope.resolve(
                AIServiceFactory.config().Pod_Profile_Name__c);
            return new Map<String, Object>{
                'built' => built,
                'scopeNote' => scope.note,
                'profileFound' => scope.profileFound,
                'ownedObjects' => scope.owned.size(),
                'nodes' => built ? nodeCountOf(file) : 0,
                'edges' => built ? edgeCountOf(file) : 0,
                'sizeKb' => built ? file.get('kb') : 0,
                'jobError' => jobs.isEmpty() ? null : jobs[0].ExtendedStatus,
                'jobStatus' => jobs.isEmpty() ? null : jobs[0].Status,
                'jobDone' => jobs.isEmpty() ? 0 : jobs[0].JobItemsProcessed,
                'jobTotal' => jobs.isEmpty() ? 0 : jobs[0].TotalJobItems,
                'jobErrors' => jobs.isEmpty() ? 0 : jobs[0].NumberOfErrors
            };
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    private static Integer nodeCountOf(Map<String, Object> file) {
        AIGraphMemory g = AIGraphMemory.load(AIGraphFileStore.COMBINED);
        return g == null ? 0 : g.nodeCount;
    }

    private static Integer edgeCountOf(Map<String, Object> file) {
        AIGraphMemory g = AIGraphMemory.load(AIGraphFileStore.COMBINED);
        return g == null ? 0 : g.edgeCount;
    }

    private static Integer elapsed(Long t0) {
        return (Integer) (System.currentTimeMillis() - t0);
    }

    /**
     * Start a request from the sentence alone: no type, no model.
     *
     * Both used to be asked for on the entry screen. The type is what the
     * analysis is for, and the model is irrelevant until there is something
     * worth generating.
     */
    @AuraEnabled
    public static Id createRequest(String requestText) {
        try {
            return AIChangeRequestService.create(requestText).Id;
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    /** Which model to ask for the logic. Only offered after gate 1. */
    @AuraEnabled
    public static ConsoleView chooseModel(Id requestId, String model) {
        try {
            AIChangeRequestService.chooseModel(requestId, model);
            return getView(requestId);
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    @AuraEnabled
    public static ConsoleView runAnalysis(Id requestId) {
        try {
            AIChangeRequestService.analyze(requestId);
            return getView(requestId);
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    @AuraEnabled
    public static ConsoleView approveAnalysis(Id requestId) {
        try {
            AIChangeRequestService.approveAnalysis(requestId);
            return getView(requestId);
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    @AuraEnabled
    public static ConsoleView approveCode(Id requestId) {
        try {
            AIChangeRequestService.approveCode(requestId);
            return getView(requestId);
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    @AuraEnabled
    public static ConsoleView rejectRequest(Id requestId, String reason) {
        try {
            AIChangeRequestService.reject(requestId, reason);
            return getView(requestId);
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    @AuraEnabled
    public static ConsoleView getView(Id requestId) {
        try {
            ConsoleView v = new ConsoleView();
            v.request = [
                SELECT Id, Name, Request_Text__c, Request_Type__c, Model__c, Pod__c,
                       Status__c, Snapshot_Id__c, Analysis_Summary__c,
                       Jira_Issue_Key__c, Jira_Issue_Url__c, Error_Message__c,
                       Analysis_Approved_By__r.Name, Analysis_Approved_At__c,
                       Code_Approved_By__r.Name, Code_Approved_At__c
                FROM AI_Change_Request__c
                WHERE Id = :requestId WITH USER_MODE LIMIT 1];
            v.findings = [
                SELECT Id, Node_Id__c, Node_Type__c, Node_Name__c, Impact__c,
                       Risk_Tier__c, Source_System__c, Relationship_Path__c,
                       Provenance__c, Confidence__c
                FROM AI_Graph_Finding__c
                WHERE Change_Request__c = :requestId
                WITH USER_MODE
                ORDER BY Impact__c, Risk_Tier__c DESC];
            v.artifacts = [
                SELECT Id, Metadata_Type__c, Api_Name__c, Operation__c,
                       Source_Body__c, Diff_Summary__c, Deploy_Status__c,
                       Deploy_Message__c
                FROM AI_Generated_Artifact__c
                WHERE Change_Request__c = :requestId WITH USER_MODE];
            v.testResults = [
                SELECT Id, Test_Class__c, Test_Method__c, Outcome__c,
                       Message__c, Run_Time_Ms__c
                FROM AI_Test_Result__c
                WHERE Change_Request__c = :requestId WITH USER_MODE];

            List<AIContextSlice.Finding> slice = new List<AIContextSlice.Finding>();
            for (AI_Graph_Finding__c f : v.findings) {
                slice.add(AIContextSlice.build(f.Node_Id__c, f.Node_Type__c,
                    f.Node_Name__c, f.Relationship_Path__c, f.Impact__c,
                    f.Risk_Tier__c, f.Source_System__c, f.Provenance__c));
            }
            v.verdict = AIReuseAnalyzer.assess(
                AIRequestIntent.parse(v.request.Request_Text__c), slice);
            return v;
        } catch (Exception e) {
            throw asAura(e);
        }
    }

    private static AuraHandledException asAura(Exception e) {
        AuraHandledException ex = new AuraHandledException(e.getMessage());
        ex.setMessage(e.getMessage());
        return ex;
    }
}
