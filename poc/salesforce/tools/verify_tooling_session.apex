/*
 * The same five Tooling API questions, without the Named Credential.
 *
 * Use this when verify_tooling_api.apex returns 401 INVALID_SESSION_ID. That
 * error means the OAuth setup is not yet handing over a token, which is a
 * configuration problem that can take a while to chase. This script sidesteps
 * it entirely and answers the questions that actually decide what gets built.
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run. Read-only: every call is a GET.
 *
 * ---------------------------------------------------------------------------
 * THIS IS A DIAGNOSTIC, NOT THE PRODUCTION PATH.
 *
 * UserInfo.getSessionId() returns a usable session in an interactive
 * anonymous block. It does NOT reliably return an API-enabled session in
 * asynchronous Apex, and the graph export is a Queueable. So the Named
 * Credential still has to be made to work before the flow reader can ship.
 * This only decouples "is the OAuth config right" from "is the data worth
 * having", so the second question stops waiting on the first.
 * ---------------------------------------------------------------------------
 *
 * ONE PREREQUISITE. Apex cannot call any host without permission, including
 * its own org:
 *
 *   Setup > Security > Remote Site Settings > New Remote Site
 *     Remote Site Name: Self_Tooling_Probe
 *     Remote Site URL:  your My Domain URL, which this script prints on its
 *                       first line if you run it before creating the setting
 *     Active: checked
 *
 * Delete that remote site once the Named Credential works. It exists for this
 * probe and nothing else.
 */

String API_VERSION = 'v59.0';
String base = URL.getOrgDomainUrl().toExternalForm();
String token = UserInfo.getSessionId();

System.debug('My Domain URL: ' + base);
System.debug('   ^ this is the value the Named Credential URL must have, and '
    + 'the Remote Site URL this script needs.');
System.debug('session available: ' + (token != null));

// ---------------------------------------------------------------- helper ---
// Anonymous blocks cannot declare methods, so the request is built inline
// each time. Repetitive on purpose: it stays paste-and-run.

// ---- 1. does a Tooling call work at all? ----------------------------------
HttpRequest ping = new HttpRequest();
ping.setEndpoint(base + '/services/data/' + API_VERSION + '/tooling/query/?q='
    + EncodingUtil.urlEncode('SELECT Id, Name FROM ApexClass LIMIT 1', 'UTF-8'));
ping.setMethod('GET');
ping.setHeader('Authorization', 'Bearer ' + token);
ping.setTimeout(60000);

Boolean connected = false;
try {
    HttpResponse r = new Http().send(ping);
    System.debug('1. connectivity · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(400));
    connected = r.getStatusCode() == 200;
} catch (Exception e) {
    System.debug('1. FAILED: ' + e.getMessage());
    System.debug('   "Unauthorized endpoint" here means the Remote Site '
        + 'Setting above has not been created yet. Create it with the My '
        + 'Domain URL printed on the first line.');
}

if (!connected) {
    System.debug('STOPPING: the rest would repeat the same error.');
} else {

// ---- 2. how big is the job? -----------------------------------------------
HttpRequest countReq = new HttpRequest();
countReq.setEndpoint(base + '/services/data/' + API_VERSION + '/tooling/query/?q='
    + EncodingUtil.urlEncode(
        'SELECT Id FROM Flow WHERE Status = \'Active\'', 'UTF-8'));
countReq.setMethod('GET');
countReq.setHeader('Authorization', 'Bearer ' + token);
countReq.setTimeout(60000);

String flowId;
try {
    HttpResponse r = new Http().send(countReq);
    System.debug('2. active flows · HTTP ' + r.getStatusCode());
    if (r.getStatusCode() == 200) {
        Map<String, Object> parsed =
            (Map<String, Object>) JSON.deserializeUntyped(r.getBody());
        System.debug('   totalSize: ' + parsed.get('totalSize')
            + ' · done: ' + parsed.get('done'));
        List<Object> records = (List<Object>) parsed.get('records');
        if (records != null && !records.isEmpty()) {
            flowId = (String) ((Map<String, Object>) records[0]).get('Id');
            System.debug('   sample flow id: ' + flowId);
        }
    } else {
        System.debug('   body: ' + r.getBody().abbreviate(400));
    }
} catch (Exception e) {
    System.debug('2. FAILED: ' + e.getMessage());
}

// ---- 3. can a flow's internals be read? -----------------------------------
// The question the whole Tooling API exercise exists to answer: does the
// retrieve carry recordCreates and recordUpdates, which is what a flow DOES.
if (flowId != null) {
    HttpRequest metaReq = new HttpRequest();
    metaReq.setEndpoint(base + '/services/data/' + API_VERSION
        + '/tooling/sobjects/Flow/' + flowId);
    metaReq.setMethod('GET');
    metaReq.setHeader('Authorization', 'Bearer ' + token);
    metaReq.setTimeout(60000);
    try {
        HttpResponse r = new Http().send(metaReq);
        String body = r.getBody();
        System.debug('3. flow metadata · HTTP ' + r.getStatusCode()
            + ' · ' + body.length() + ' characters');
        System.debug('   mentions recordCreates: ' + body.contains('recordCreates'));
        System.debug('   mentions recordUpdates: ' + body.contains('recordUpdates'));
        System.debug('   mentions recordLookups: ' + body.contains('recordLookups'));
        System.debug('   mentions subflows:      ' + body.contains('subflows'));
        System.debug('   first 900 characters: ' + body.abbreviate(900));
    } catch (Exception e) {
        System.debug('3. FAILED: ' + e.getMessage());
    }
} else {
    System.debug('3. skipped: no active flow id came back from step 2.');
}

// ---- 4. is Metadata really one record per call? ---------------------------
HttpRequest manyReq = new HttpRequest();
manyReq.setEndpoint(base + '/services/data/' + API_VERSION + '/tooling/query/?q='
    + EncodingUtil.urlEncode(
        'SELECT Id, Metadata FROM Flow WHERE Status = \'Active\' LIMIT 5',
        'UTF-8'));
manyReq.setMethod('GET');
manyReq.setHeader('Authorization', 'Bearer ' + token);
manyReq.setTimeout(60000);
try {
    HttpResponse r = new Http().send(manyReq);
    System.debug('4. SELECT Metadata, LIMIT 5 · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(500));
    if (r.getStatusCode() == 200) {
        System.debug('   SIGNAL: several records came back with Metadata '
            + 'selected, so the one-record-per-call rule does not apply here '
            + 'and the flow reader gets far simpler.');
    } else {
        System.debug('   As expected: one record per call, so reading every '
            + 'flow needs a chained Queueable across transactions.');
    }
} catch (Exception e) {
    System.debug('4. FAILED: ' + e.getMessage());
}

// ---- 5. is the dependency API available? ----------------------------------
HttpRequest depReq = new HttpRequest();
depReq.setEndpoint(base + '/services/data/' + API_VERSION + '/tooling/query/?q='
    + EncodingUtil.urlEncode(
        'SELECT MetadataComponentName, RefMetadataComponentName '
        + 'FROM MetadataComponentDependency LIMIT 5', 'UTF-8'));
depReq.setMethod('GET');
depReq.setHeader('Authorization', 'Bearer ' + token);
depReq.setTimeout(60000);
try {
    HttpResponse r = new Http().send(depReq);
    System.debug('5. MetadataComponentDependency · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(500));
    if (r.getStatusCode() != 200) {
        System.debug('   Usually means this user lacks View All Data. Flow '
            + 'internals do not need it, so this alone is not a blocker.');
    }
} catch (Exception e) {
    System.debug('5. FAILED: ' + e.getMessage());
}

}

System.debug('callouts used: ' + Limits.getCallouts()
    + ' of ' + Limits.getLimitCallouts());
