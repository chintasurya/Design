/**
 * State machine for one AI change request.
 *
 * Every transition is recorded on the record itself, so the audit trail is
 * queryable rather than buried in logs. The two approval gates are explicit
 * states, not flags: a request cannot reach code generation without passing
 * through Awaiting Analysis Approval, and cannot reach deployment without
 * passing through Awaiting Code Approval.
 */
public with sharing class AIChangeRequestService {

    public class StateException extends Exception {}

    public static final String DRAFT             = 'Draft';
    public static final String ANALYZING         = 'Analyzing';
    public static final String AWAIT_ANALYSIS    = 'Awaiting Analysis Approval';
    public static final String TICKET_CREATED    = 'Ticket Created';
    public static final String GENERATING        = 'Generating';
    public static final String AWAIT_CODE        = 'Awaiting Code Approval';
    public static final String DEPLOYING         = 'Deploying';
    public static final String TESTING           = 'Testing';
    public static final String COMPLETE          = 'Complete';
    public static final String REJECTED          = 'Rejected';
    public static final String FAILED            = 'Failed';

    private static final Map<String, Set<String>> ALLOWED =
        new Map<String, Set<String>>{
            DRAFT          => new Set<String>{ ANALYZING, REJECTED },
            ANALYZING      => new Set<String>{ AWAIT_ANALYSIS, FAILED },
            AWAIT_ANALYSIS => new Set<String>{ TICKET_CREATED, REJECTED },
            TICKET_CREATED => new Set<String>{ GENERATING, FAILED },
            GENERATING     => new Set<String>{ AWAIT_CODE, FAILED },
            AWAIT_CODE     => new Set<String>{ DEPLOYING, REJECTED },
            DEPLOYING      => new Set<String>{ TESTING, FAILED },
            TESTING        => new Set<String>{ COMPLETE, FAILED }
        };

    public static AI_Change_Request__c create(String requestText,
                                              String requestType,
                                              String model) {
        if (String.isBlank(requestText)) {
            throw new StateException('Describe the change before submitting it.');
        }
        AI_Change_Request__c req = new AI_Change_Request__c(
            Request_Text__c  = requestText,
            Request_Type__c  = requestType,
            Model__c         = model,
            Pod__c           = 'Network Services',
            Status__c        = DRAFT,
            Correlation_Id__c = generateCorrelationId()
        );
        insert req;
        return req;
    }

    /** Runs the graph query and parks the request at the first approval gate. */
    public static void analyze(Id requestId) {
        AI_Change_Request__c req = load(requestId);
        transitionTo(req, ANALYZING);

        try {
            AIContextSlice slice = AIServiceFactory.contextGraph().query(req);

            delete [SELECT Id FROM AI_Graph_Finding__c
                    WHERE Change_Request__c = :requestId];
            insert slice.toRecords(requestId);

            req.Snapshot_Id__c      = slice.snapshotId;
            req.Analysis_Summary__c = slice.summary;
            req.Error_Message__c    = null;
            transitionTo(req, AWAIT_ANALYSIS);
        } catch (Exception e) {
            fail(req, e.getMessage());
            throw e;
        }
    }

    public static void approveAnalysis(Id requestId) {
        AI_Change_Request__c req = load(requestId);
        req.Analysis_Approved_By__c = UserInfo.getUserId();
        req.Analysis_Approved_At__c = System.now();
        transitionTo(req, TICKET_CREATED);
    }

    public static void approveCode(Id requestId) {
        AI_Change_Request__c req = load(requestId);
        req.Code_Approved_By__c = UserInfo.getUserId();
        req.Code_Approved_At__c = System.now();
        transitionTo(req, DEPLOYING);
    }

    public static void reject(Id requestId, String reason) {
        AI_Change_Request__c req = load(requestId);
        req.Error_Message__c = reason;
        transitionTo(req, REJECTED);
    }

    public static void fail(AI_Change_Request__c req, String message) {
        req.Error_Message__c = message;
        req.Status__c = FAILED;
        update req;
    }

    private static void transitionTo(AI_Change_Request__c req, String target) {
        Set<String> allowed = ALLOWED.get(req.Status__c);
        Boolean legal = target == REJECTED || target == FAILED
                     || (allowed != null && allowed.contains(target));
        if (!legal) {
            throw new StateException(
                'Cannot move from "' + req.Status__c + '" to "' + target + '".');
        }
        req.Status__c = target;
        update req;
    }

    private static AI_Change_Request__c load(Id requestId) {
        List<AI_Change_Request__c> rows = [
            SELECT Id, Status__c, Request_Text__c, Request_Type__c, Model__c,
                   Pod__c, Correlation_Id__c, Snapshot_Id__c, Analysis_Summary__c,
                   Analysis_Approved_By__c, Analysis_Approved_At__c,
                   Code_Approved_By__c, Code_Approved_At__c, Error_Message__c
            FROM AI_Change_Request__c
            WHERE Id = :requestId
            WITH USER_MODE
            LIMIT 1];
        if (rows.isEmpty()) {
            throw new StateException('Change request not found or not visible.');
        }
        return rows[0];
    }

    private static String generateCorrelationId() {
        Blob b = Crypto.generateAesKey(128);
        String h = EncodingUtil.convertToHex(b);
        return h.substring(0, 8) + '-' + h.substring(8, 12) + '-'
             + h.substring(12, 16) + '-' + h.substring(16, 20) + '-'
             + h.substring(20, 32);
    }
}
