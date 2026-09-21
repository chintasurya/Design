/*
 * Does the Tooling API Named Credential actually work, and what shape is the
 * data behind it?
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run, then read the USER_DEBUG lines. Read-only: every call is a
 * GET, nothing is created, updated or deleted.
 *
 * Run this before anything is built on top of the credential. Four
 * assumptions are being made about this API and all four are worth checking
 * rather than trusting:
 *
 *   1. the callout authenticates and returns JSON, not a login page
 *   2. Flow.Metadata is readable, which is the whole reason for the setup
 *   3. selecting Metadata really is limited to one record per call
 *   4. MetadataComponentDependency is available to this user
 *
 * Setup instructions: TOOLING_API_SETUP.md
 */

String CREDENTIAL = 'AI_Tooling_API';    // must match the Named Credential name
String API_VERSION = 'v59.0';

// ---------------------------------------------------------------- helper ---
// Declared as a variable so Execute Anonymous can call it; anonymous blocks
// cannot declare methods.
HttpResponse lastResponse;

// ---- 1. does it authenticate at all? --------------------------------------
String soql = 'SELECT COUNT() FROM Flow WHERE Status = \'Active\'';
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:' + CREDENTIAL + '/services/data/' + API_VERSION
    + '/tooling/query/?q=' + EncodingUtil.urlEncode(soql, 'UTF-8'));
req.setMethod('GET');
req.setTimeout(60000);

try {
    lastResponse = new Http().send(req);
    System.debug('1. COUNT of active flows · HTTP ' + lastResponse.getStatusCode());
    String body = lastResponse.getBody();
    System.debug('   body: ' + body.abbreviate(500));
    if (body.startsWith('<')) {
        System.debug('   SIGNAL: that is HTML, not JSON. The Named Credential '
            + 'URL is almost certainly test.salesforce.com, which serves login '
            + 'pages. It must be the My Domain sandbox URL.');
    }
} catch (Exception e) {
    System.debug('1. FAILED: ' + e.getMessage());
    System.debug('   A callout exception here usually means the Named '
        + 'Credential does not exist under that exact name, or its '
        + 'Authentication Status is not Authenticated.');
}

// ---- 2. can a flow's internals be read? -----------------------------------
// This is the question the whole setup exists to answer. Metadata carries
// recordCreates and recordUpdates, which is what a Flow actually DOES.
String oneFlow = 'SELECT Id, FullName FROM Flow WHERE Status = \'Active\' LIMIT 1';
HttpRequest idReq = new HttpRequest();
idReq.setEndpoint('callout:' + CREDENTIAL + '/services/data/' + API_VERSION
    + '/tooling/query/?q=' + EncodingUtil.urlEncode(oneFlow, 'UTF-8'));
idReq.setMethod('GET');
idReq.setTimeout(60000);

String flowId;
try {
    HttpResponse r = new Http().send(idReq);
    System.debug('2a. one flow id · HTTP ' + r.getStatusCode());
    Map<String, Object> parsed =
        (Map<String, Object>) JSON.deserializeUntyped(r.getBody());
    List<Object> records = (List<Object>) parsed.get('records');
    if (records != null && !records.isEmpty()) {
        flowId = (String) ((Map<String, Object>) records[0]).get('Id');
        System.debug('    flow id: ' + flowId);
    } else {
        System.debug('    no active flows returned: ' + r.getBody().abbreviate(300));
    }
} catch (Exception e) {
    System.debug('2a. FAILED: ' + e.getMessage());
}

if (flowId != null) {
    HttpRequest metaReq = new HttpRequest();
    metaReq.setEndpoint('callout:' + CREDENTIAL + '/services/data/' + API_VERSION
        + '/tooling/sobjects/Flow/' + flowId);
    metaReq.setMethod('GET');
    metaReq.setTimeout(60000);
    try {
        HttpResponse r = new Http().send(metaReq);
        String body = r.getBody();
        System.debug('2b. flow metadata · HTTP ' + r.getStatusCode()
            + ' · ' + body.length() + ' characters');
        System.debug('    mentions recordCreates: ' + body.contains('recordCreates'));
        System.debug('    mentions recordUpdates: ' + body.contains('recordUpdates'));
        System.debug('    mentions subflows: ' + body.contains('subflows'));
        System.debug('    first 800: ' + body.abbreviate(800));
    } catch (Exception e) {
        System.debug('2b. FAILED: ' + e.getMessage());
    }
}

// ---- 3. is Metadata really one record per call? ---------------------------
// If this returns several records, the flow reader does not need to be a
// chained Queueable and the whole job gets much smaller.
String manyMeta = 'SELECT Id, Metadata FROM Flow WHERE Status = \'Active\' LIMIT 5';
HttpRequest manyReq = new HttpRequest();
manyReq.setEndpoint('callout:' + CREDENTIAL + '/services/data/' + API_VERSION
    + '/tooling/query/?q=' + EncodingUtil.urlEncode(manyMeta, 'UTF-8'));
manyReq.setMethod('GET');
manyReq.setTimeout(60000);
try {
    HttpResponse r = new Http().send(manyReq);
    System.debug('3. SELECT Metadata with LIMIT 5 · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(600));
    if (r.getStatusCode() == 200) {
        System.debug('   SIGNAL: several records came back with Metadata '
            + 'selected. The one-record-per-call constraint may not apply '
            + 'here, which makes the flow reader far simpler.');
    }
} catch (Exception e) {
    System.debug('3. FAILED: ' + e.getMessage());
}

// ---- 4. is the dependency API available? ----------------------------------
String deps = 'SELECT MetadataComponentName, RefMetadataComponentName '
            + 'FROM MetadataComponentDependency LIMIT 5';
HttpRequest depReq = new HttpRequest();
depReq.setEndpoint('callout:' + CREDENTIAL + '/services/data/' + API_VERSION
    + '/tooling/query/?q=' + EncodingUtil.urlEncode(deps, 'UTF-8'));
depReq.setMethod('GET');
depReq.setTimeout(60000);
try {
    HttpResponse r = new Http().send(depReq);
    System.debug('4. MetadataComponentDependency · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(600));
    if (r.getStatusCode() != 200) {
        System.debug('   This usually means the named principal lacks View '
            + 'All Data. Real dependency edges need it; flow internals do not.');
    }
} catch (Exception e) {
    System.debug('4. FAILED: ' + e.getMessage());
}

System.debug('callouts used: ' + Limits.getCallouts()
    + ' of ' + Limits.getLimitCallouts());
