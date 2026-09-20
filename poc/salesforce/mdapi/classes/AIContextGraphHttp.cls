/**
 * Live graph layer, reached through a Named Credential.
 *
 * Kept deliberately thin. Traversal, reuse detection and risk tiering all
 * happen in Semantica; this class only moves the request out and the slice
 * back. That is what keeps the graph logic in one place rather than two.
 */
public class AIContextGraphHttp implements AIContextGraphService {

    public class CalloutException extends Exception {}

    private static final Integer TIMEOUT_MS = 100000;

    public AIContextSlice query(AI_Change_Request__c request) {
        AI_Poc_Config__mdt cfg = AIServiceFactory.config();

        Map<String, Object> payload = new Map<String, Object>{
            'requestId'     => request.Id,
            'correlationId' => request.Correlation_Id__c,
            'requestText'   => request.Request_Text__c,
            'requestType'   => request.Request_Type__c,
            'pod'           => request.Pod__c,
            'model'         => request.Model__c
        };

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:' + cfg.Context_Named_Credential__c
                        + cfg.Context_Query_Path__c);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setTimeout(TIMEOUT_MS);
        req.setBody(JSON.serialize(payload));

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() < 200 || res.getStatusCode() >= 300) {
            throw new CalloutException('Context service returned HTTP '
                + res.getStatusCode() + ': ' + res.getBody().abbreviate(500));
        }
        return (AIContextSlice) JSON.deserialize(res.getBody(), AIContextSlice.class);
    }
}
