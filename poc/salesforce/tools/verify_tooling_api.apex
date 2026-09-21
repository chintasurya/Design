/*
 * Does the Tooling API Named Credential actually work, and what shape is the
 * data behind it?
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run, then read the USER_DEBUG lines. Read-only: every call is a
 * GET. Nothing is created, updated or deleted, in the org or anywhere else.
 *
 * Run this before anything is built on top of the credential. Five things are
 * being assumed about this API and all five are worth checking rather than
 * trusting:
 *
 *   1. the callout authenticates and returns JSON, not a login page
 *   2. how many active flows there are, which sets the size of the job
 *   3. a flow's Metadata is readable, which is the whole reason for the setup
 *   4. whether selecting Metadata really is one record per call
 *   5. whether MetadataComponentDependency is available to this user
 *
 * Setup instructions: TOOLING_API_SETUP.md
 */

// The Named Credential's API name, exactly as it appears in Setup. If you
// named it something else, change this one line; nothing else reads it yet.
String CREDENTIAL = 'AI_Tooling_API';
String API_VERSION = 'v59.0';

String base = 'callout:' + CREDENTIAL + '/services/data/' + API_VERSION;

// ---- 1. does it authenticate at all? --------------------------------------
// Deliberately the dullest possible query. ApexClass is readable through the
// Tooling API in every org, so a failure here is the credential, never the
// query.
HttpRequest ping = new HttpRequest();
ping.setEndpoint(base + '/tooling/query/?q='
    + EncodingUtil.urlEncode('SELECT Id, Name FROM ApexClass LIMIT 1', 'UTF-8'));
ping.setMethod('GET');
ping.setTimeout(60000);

Boolean connected = false;
try {
    HttpResponse r = new Http().send(ping);
    String body = r.getBody();
    System.debug('1. connectivity · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + body.abbreviate(400));
    connected = r.getStatusCode() == 200;
    if (body.startsWith('<')) {
        System.debug('   SIGNAL: that is HTML, not JSON. The Named Credential '
            + 'URL is almost certainly test.salesforce.com, which serves login '
            + 'pages rather than the API. It must be the My Domain sandbox URL, '
            + 'ending .sandbox.my.salesforce.com');
    } else if (r.getStatusCode() == 401) {
        System.debug('   SIGNAL: 401. The Named Credential exists but is not '
            + 'authenticated. Open it in Setup: Authentication Status must read '
            + '"Authenticated as <user>", not Pending.');
    } else if (r.getStatusCode() == 403) {
        System.debug('   SIGNAL: 403. Authenticated, but that user lacks API '
            + 'Enabled or View Setup and Configuration.');
    }
} catch (Exception e) {
    System.debug('1. FAILED before any response: ' + e.getMessage());
    System.debug('   Usually the Named Credential does not exist under the name '
        + 'in CREDENTIAL above. Check Setup > Named Credentials for the exact '
        + 'API name.');
}

// Everything below needs step 1 to have worked. Running it anyway just prints
// the same failure four more times.
if (!connected) {
    System.debug('STOPPING: connectivity failed, so the rest would only repeat '
        + 'the same error. Fix the credential first.');
} else {

// ---- 2. how big is the job? -----------------------------------------------
// totalSize on an unlimited query is the honest count of flow bodies that
// would have to be read, which decides whether this needs chaining at all.
HttpRequest countReq = new HttpRequest();
countReq.setEndpoint(base + '/tooling/query/?q='
    + EncodingUtil.urlEncode(
        'SELECT Id FROM Flow WHERE Status = \'Active\'', 'UTF-8'));
countReq.setMethod('GET');
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
// This is the question the whole setup exists to answer. Retrieving a single
// flow returns its Metadata, which carries recordCreates and recordUpdates:
// what the flow actually DOES, rather than merely that it exists.
if (flowId != null) {
    HttpRequest metaReq = new HttpRequest();
    metaReq.setEndpoint(base + '/tooling/sobjects/Flow/' + flowId);
    metaReq.setMethod('GET');
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
// If several records come back, the flow reader does not need to be a chained
// Queueable and the whole job gets much smaller. Worth one call to find out.
HttpRequest manyReq = new HttpRequest();
manyReq.setEndpoint(base + '/tooling/query/?q='
    + EncodingUtil.urlEncode(
        'SELECT Id, Metadata FROM Flow WHERE Status = \'Active\' LIMIT 5',
        'UTF-8'));
manyReq.setMethod('GET');
manyReq.setTimeout(60000);
try {
    HttpResponse r = new Http().send(manyReq);
    System.debug('4. SELECT Metadata, LIMIT 5 · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(500));
    if (r.getStatusCode() == 200) {
        System.debug('   SIGNAL: several records came back with Metadata '
            + 'selected, so the one-record-per-call rule does not apply here. '
            + 'That makes the flow reader far simpler.');
    } else {
        System.debug('   As expected: Metadata is one record per call, so '
            + 'reading every flow needs a chained Queueable across '
            + 'transactions.');
    }
} catch (Exception e) {
    System.debug('4. FAILED: ' + e.getMessage());
}

// ---- 5. is the dependency API available? ----------------------------------
HttpRequest depReq = new HttpRequest();
depReq.setEndpoint(base + '/tooling/query/?q='
    + EncodingUtil.urlEncode(
        'SELECT MetadataComponentName, RefMetadataComponentName '
        + 'FROM MetadataComponentDependency LIMIT 5', 'UTF-8'));
depReq.setMethod('GET');
depReq.setTimeout(60000);
try {
    HttpResponse r = new Http().send(depReq);
    System.debug('5. MetadataComponentDependency · HTTP ' + r.getStatusCode());
    System.debug('   body: ' + r.getBody().abbreviate(500));
    if (r.getStatusCode() != 200) {
        System.debug('   Usually means the named principal lacks View All Data. '
            + 'Real dependency edges need it; flow internals do not, so this '
            + 'failing on its own is not a blocker.');
    }
} catch (Exception e) {
    System.debug('5. FAILED: ' + e.getMessage());
}

}

System.debug('callouts used: ' + Limits.getCallouts()
    + ' of ' + Limits.getLimitCallouts());
