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
    }

    @AuraEnabled
    public static Id createRequest(String requestText, String requestType, String model) {
        try {
            return AIChangeRequestService.create(requestText, requestType, model).Id;
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
