/**
 * Canned graph responses so the console is demonstrable with no backend.
 *
 * Shape and provenance match what the live service returns, so swapping in
 * AIContextGraphHttp changes nothing downstream. Replace the fixtures with
 * real node ids from the discovery run before showing this to anyone.
 */
public class AIContextGraphStub implements AIContextGraphService {

    public AIContextSlice query(AI_Change_Request__c request) {
        AIContextSlice slice = new AIContextSlice();
        slice.snapshotId = 'stub-' + String.valueOf(Date.today());
        slice.summary =
            'Stubbed graph response. 5 nodes reached across 3 source systems. '
          + 'Configure AI_Poc_Config__mdt.Default to point at the live service.';

        slice.findings.add(build('sobj:HFN__c', 'SObject', 'HFN',
            'Direct target of the request', 'Direct', 'High', 'Salesforce',
            'SALESFORCE_METADATA objects/HFN__c.object-meta.xml', 1.0));
        slice.findings.add(build('flow:HFN_Generation', 'Flow', 'HFN Generation',
            'FLOW_UPDATES_SOBJECT -> sobj:HFN__c', 'One Hop', 'High', 'Salesforce',
            'SALESFORCE_METADATA flows/HFN_Generation.flow-meta.xml', 1.0));
        slice.findings.add(build('apex:HFNGenerationService', 'ApexClass',
            'HFNGenerationService',
            'APEX_REFERENCES_SOBJECT -> sobj:HFN__c', 'One Hop', 'High', 'Salesforce',
            'GIT force-app/main/default/classes/HFNGenerationService.cls', 1.0));
        slice.findings.add(build('req:NS-1234', 'Requirement',
            'HFN must not duplicate on reactivation',
            'REQUIREMENT_IMPLEMENTED_BY -> apex:HFNGenerationService',
            'Two Hop', 'Medium', 'Jira',
            'JIRA_ISSUE NS-1234 updated 2026-09-02', 1.0));
        slice.findings.add(build('rule:hfn-requires-active-hpf', 'BusinessRule',
            'HFN requires an active HPF',
            'SECTION_DEFINES_RULE -> RULE_CONSTRAINS_SOBJECT -> sobj:HFN__c',
            'Two Hop', 'High', 'Confluence',
            'CONFLUENCE_SECTION page 88213 v7 "Generation Rules"', 1.0));
        return slice;
    }

    private AIContextSlice.Finding build(String id, String type, String name,
            String path, String impact, String risk, String system,
            String provenance, Decimal confidence) {
        AIContextSlice.Finding f = new AIContextSlice.Finding();
        f.nodeId = id;
        f.nodeType = type;
        f.nodeName = name;
        f.relationshipPath = path;
        f.impact = impact;
        f.riskTier = risk;
        f.sourceSystem = system;
        f.provenance = provenance;
        f.artifactHash = 'sha256:stub';
        f.confidence = confidence;
        return f;
    }
}
