/**
 * Real-time context search over the Network Services footprint.
 *
 * Runs as four observable steps rather than one opaque call, so the console
 * can show what it is doing while it does it. Each step is real work: parse,
 * resolve scope, search live metadata, assess. Nothing is simulated and no
 * step is a timer.
 *
 * Jira and Confluence are deliberately not read here. They are write targets
 * for this POC: a ticket on approval, a page on completion.
 */
public with sharing class AIContextGraphLive implements AIContextGraphService {

    public class Step {
        @AuraEnabled public String key;
        @AuraEnabled public String label;
        @AuraEnabled public String detail;
        @AuraEnabled public Integer elapsedMs;
        public Step(String k, String l, String d, Integer ms) {
            key = k; label = l; detail = d; elapsedMs = ms;
        }
    }

    /** One shot, for the interface. The console uses the stepped methods. */
    public AIContextSlice query(AI_Change_Request__c request) {
        AIRequestIntent intent = AIRequestIntent.parse(request.Request_Text__c);
        AINetworkServicesScope scope = AINetworkServicesScope.resolve(
            AIServiceFactory.config().Pod_Profile_Name__c);
        AISalesforceMetadataSource.Result found =
            AISalesforceMetadataSource.search(intent, scope);

        AIContextSlice slice = new AIContextSlice();
        slice.snapshotId = 'live-' + System.now().format('yyyyMMdd-HHmmss');
        slice.findings = found.findings;
        slice.summary = summarize(intent, scope, found);
        return slice;
    }

    public static String summarize(AIRequestIntent intent,
                                   AINetworkServicesScope scope,
                                   AISalesforceMetadataSource.Result found) {
        List<String> parts = new List<String>();
        parts.add('Read: ' + intent.summary);
        parts.add(scope.profileFound
            ? 'Scope: ' + scope.readable.size() + ' pod objects'
            : 'Scope: whole org (pod profile not found)');
        parts.add(found.findings.size() + ' components across '
            + typeCount(found.findings) + ' types');
        return String.join(parts, ' · ');
    }

    private static Integer typeCount(List<AIContextSlice.Finding> findings) {
        Set<String> types = new Set<String>();
        for (AIContextSlice.Finding f : findings) {
            types.add(f.nodeType);
        }
        return types.size();
    }
}
