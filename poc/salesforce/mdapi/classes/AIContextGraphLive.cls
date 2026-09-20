/**
 * Real-time context search across the sources that are actually reachable.
 *
 * Salesforce metadata is always searched, because Apex can read the running
 * org with no configuration. Jira and Confluence join in once their Named
 * Credentials exist. Every source reports whether it ran, so the summary line
 * tells you exactly what the answer was built from and what it was missing.
 *
 * This is the honest interim. It is federated live search, not graph
 * traversal: no precomputed typed edges, no multi-hop blast radius, no reuse
 * detection across capabilities. Those arrive with the Semantica service
 * behind AIContextGraphHttp, and nothing above this class changes when they do.
 */
public with sharing class AIContextGraphLive implements AIContextGraphService {

    public AIContextSlice query(AI_Change_Request__c request) {
        AI_Poc_Config__mdt cfg = AIServiceFactory.config();
        AIContextSlice slice = new AIContextSlice();
        slice.snapshotId = 'live-' + System.now().format('yyyyMMdd-HHmmss');

        Set<String> terms = AISalesforceMetadataSource.extractTerms(request.Request_Text__c);
        List<String> report = new List<String>();

        AISalesforceMetadataSource.Result sf = AISalesforceMetadataSource.search(terms);
        slice.findings.addAll(sf.findings);
        report.add('Salesforce: ' + sf.findings.size() + ' live metadata matches');

        AIAtlassianSource.Result jira = AIAtlassianSource.searchJira(
            cfg.Jira_Named_Credential__c, cfg.Jira_Project_Key__c, terms);
        slice.findings.addAll(jira.findings);
        report.add('Jira: ' + (jira.note != null
            ? jira.note : jira.findings.size() + ' issues'));

        AIAtlassianSource.Result conf = AIAtlassianSource.searchConfluence(
            cfg.Confluence_Named_Credential__c, cfg.Confluence_Space_Key__c, terms);
        slice.findings.addAll(conf.findings);
        report.add('Confluence: ' + (conf.note != null
            ? conf.note : conf.findings.size() + ' pages'));

        slice.summary = 'Searched "' + String.join(new List<String>(terms), ', ')
            + '" at ' + System.now().format('HH:mm:ss') + '. '
            + String.join(report, ' · ') + '.';
        if (slice.findings.isEmpty()) {
            slice.summary += ' Nothing matched, so there is nothing to send to a model.';
        }
        return slice;
    }
}
