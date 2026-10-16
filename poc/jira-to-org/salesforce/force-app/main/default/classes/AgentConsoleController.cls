/**
 * Apex face of the Jira-to-Org agent gateway on GCP.
 *
 * The LWC never calls out itself: every request goes through here and the
 * Agent_Gateway Named Credential, which holds the gateway URL and injects the
 * X-Gateway-Key header from its External Credential. No key or token ever
 * reaches the browser, and none is stored in this org's data.
 *
 * Each method maps to exactly one gateway route. There is deliberately no
 * generic "call any path" method.
 */
public with sharing class AgentConsoleController {

    @TestVisible
    private static final String ENDPOINT = 'callout:Agent_Gateway';
    private static final Integer TIMEOUT_MS = 120000;
    private static final Pattern RUN_ID = Pattern.compile('^[a-f0-9]{8,32}$');
    private static final Pattern TICKET_KEY = Pattern.compile('^[A-Z][A-Z0-9]{1,9}-[0-9]+$');
    private static final Pattern NODE_ID = Pattern.compile('^[a-z]+:[A-Za-z0-9_.\\-]{1,200}$');

    @AuraEnabled
    public static String status() {
        return send('GET', '/v1/status', null);
    }

    /** Connect to Codex. apiKey is optional: blank uses the key already in GCP Secret Manager. */
    @AuraEnabled
    public static String connectCodex(String apiKey) {
        Map<String, Object> body = new Map<String, Object>();
        if (String.isNotBlank(apiKey)) {
            body.put('apiKey', apiKey.trim());
        }
        return send('POST', '/v1/codex/connect', body);
    }

    /** Poll a developer's own Codex sign-in after connectCodex started it. */
    @AuraEnabled
    public static String codexLoginStatus() {
        return send('GET', '/v1/codex/login', null);
    }

    @AuraEnabled
    public static String codexLogout() {
        return send('POST', '/v1/codex/logout', new Map<String, Object>());
    }

    @AuraEnabled
    public static String listTickets(Boolean onlyOpen) {
        return send('GET', '/v1/jira/tickets?only_open=' + (onlyOpen == false ? 'false' : 'true'), null);
    }

    @AuraEnabled
    public static String askRequirementAgent(String message, String conversationId) {
        if (String.isBlank(message)) {
            throw error('Type a question about a Jira ticket first.');
        }
        Map<String, Object> body = new Map<String, Object>{ 'message' => message.trim() };
        if (String.isNotBlank(conversationId)) {
            body.put('conversationId', conversationId);
        }
        return send('POST', '/v1/requirements/chat', body);
    }

    @AuraEnabled
    public static String startDevelopment(String ticketKey, String specJson, Boolean developAnyway) {
        String key = String.isBlank(ticketKey) ? '' : ticketKey.trim().toUpperCase();
        if (!TICKET_KEY.matcher(key).matches()) {
            throw error('Not a Jira ticket key: ' + ticketKey);
        }
        Object spec;
        try {
            spec = JSON.deserializeUntyped(specJson);
        } catch (Exception e) {
            throw error('The requirement spec is not valid JSON.');
        }
        return send('POST', '/v1/developer/runs', new Map<String, Object>{
            'ticketKey' => key, 'spec' => spec, 'override' => developAnyway == true
        });
    }

    @AuraEnabled
    public static String getRun(String runId) {
        return send('GET', '/v1/runs/' + checkedRunId(runId), null);
    }

    @AuraEnabled
    public static String approveDeployment(String runId) {
        return send('POST', '/v1/runs/' + checkedRunId(runId) + '/deploy', new Map<String, Object>());
    }

    @AuraEnabled
    public static String rejectDeployment(String runId) {
        return send('POST', '/v1/runs/' + checkedRunId(runId) + '/reject', new Map<String, Object>());
    }

    @AuraEnabled
    public static String rebuildGraph() {
        return send('POST', '/v1/graph/rebuild', new Map<String, Object>());
    }

    /** Knowledge Graph tab: how the kinds of component connect. */
    @AuraEnabled
    public static String graphSchema() {
        return send('GET', '/v1/graph/schema', null);
    }

    /** Knowledge Graph tab: one component and its direct connections, by search text or node id. */
    @AuraEnabled
    public static String graphNeighbourhood(String query, String nodeId) {
        if (String.isNotBlank(nodeId)) {
            if (!NODE_ID.matcher(nodeId).matches()) {
                throw error('Not a graph node id: ' + nodeId);
            }
            return send('GET', '/v1/graph/neighbourhood?id=' + EncodingUtil.urlEncode(nodeId, 'UTF-8'), null);
        }
        if (String.isBlank(query)) {
            throw error('Type a component name to look up.');
        }
        return send('GET', '/v1/graph/neighbourhood?q=' + EncodingUtil.urlEncode(query.trim().abbreviate(200), 'UTF-8'), null);
    }

    /** Agent Dashboard tab: token usage of both agents over the last N days. */
    @AuraEnabled
    public static String usageSummary(Integer days) {
        Integer d = days == null ? 14 : Math.max(1, Math.min(90, days));
        return send('GET', '/v1/usage?days=' + d, null);
    }

    private static String checkedRunId(String runId) {
        if (String.isBlank(runId) || !RUN_ID.matcher(runId).matches()) {
            throw error('Not a run id: ' + runId);
        }
        return runId;
    }

    private static String send(String method, String path, Map<String, Object> body) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(ENDPOINT + path);
        req.setMethod(method);
        req.setTimeout(TIMEOUT_MS);
        req.setHeader('Accept', 'application/json');
        req.setHeader('X-Salesforce-User', UserInfo.getUserName());
        if (body != null) {
            req.setHeader('Content-Type', 'application/json');
            req.setBody(JSON.serialize(body));
        }
        HttpResponse res;
        try {
            res = new Http().send(req);
        } catch (System.CalloutException e) {
            throw error('Could not reach the agent gateway. Check the Agent_Gateway Named Credential URL. ('
                + e.getMessage() + ')');
        }
        Integer code = res.getStatusCode();
        if (code >= 200 && code < 300) {
            return res.getBody();
        }
        throw error(gatewayMessage(code, res.getBody()));
    }

    @TestVisible
    private static String gatewayMessage(Integer code, String responseBody) {
        String detail = responseBody;
        try {
            Object parsed = JSON.deserializeUntyped(responseBody);
            if (parsed instanceof Map<String, Object>) {
                Object d = ((Map<String, Object>) parsed).get('detail');
                if (d != null) {
                    detail = d instanceof String ? (String) d : JSON.serialize(d);
                }
            }
        } catch (Exception e) {
            detail = responseBody;
        }
        if (code == 401) {
            return 'The gateway rejected the key. Re-enter ApiKey on the Agent Gateway external credential principal.';
        }
        return 'Gateway ' + code + ': ' + (String.isBlank(detail) ? 'no detail' : detail.abbreviate(600));
    }

    private static AuraHandledException error(String message) {
        AuraHandledException e = new AuraHandledException(message);
        e.setMessage(message);
        return e;
    }
}
