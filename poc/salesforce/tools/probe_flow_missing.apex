/*
 * Why is no Flow linked to Account?
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run, then read the USER_DEBUG lines. Read-only: it queries and
 * prints, it writes nothing to the org.
 *
 * Every risky query is wrapped. A view object that refuses a filter, a sort or
 * an aggregate must degrade one answer, not kill the whole probe before the
 * cheaper answers have been printed.
 *
 * It answers five questions in order, cheapest first, because four of the five
 * possible causes need no Tooling API at all:
 *   1. is Account inside the Network Services scope, and is the profile even
 *      the right scope signal in this org?
 *   2. does FlowDefinitionView report a record-triggered flow on Account?
 *   3. did the 200-flow cap cut it off?
 *   4. did it reach the graph file?
 *   5. can flow internals be read with plain SOQL, skipping the Tooling API?
 */

String POD = 'Network Services';

// ---- 1. scope -------------------------------------------------------------
AINetworkServicesScope scope = AINetworkServicesScope.resolve(POD);
System.debug('profile matched: ' + scope.matchedProfile
    + ' (found=' + scope.profileFound + ')');
System.debug('scope size: ' + scope.owned.size()
    + ' owned, ' + scope.writable.size() + ' writable on the profile, '
    + scope.readable.size() + ' readable on the profile');
System.debug('writable via permission sets assigned to this profile\'s users: '
    + scope.permissionSetWritable.size()
    + ' (scope taken from them: ' + scope.scopeCameFromPermissionSets + ')');
System.debug('NOTE: ' + scope.note);
System.debug('Account in scope: ' + scope.covers('Account'));
System.debug('HealthcareProvider in scope: ' + scope.covers('HealthcareProvider'));
System.debug('HealthcareFacility in scope: ' + scope.covers('HealthcareFacility'));

// If the profile sees fewer objects than the permission sets do, the profile
// is the narrower signal and the whole scoping premise needs revisiting.
if (scope.permissionSetWritable.size() > scope.readable.size()) {
    System.debug('SIGNAL: permission sets grant more than the profile. '
        + 'Objects writable only via permission set, first 40: ');
    Integer shown = 0;
    for (String obj : scope.permissionSetWritable) {
        if (!scope.owned.contains(obj) && shown++ < 40) {
            System.debug('   only via permission set: ' + obj);
        }
    }
}

// ---- 2 and 3. what FlowDefinitionView reports -----------------------------
// The honest total, to compare against the 200 the exporter can read.
try {
    Integer active = [SELECT COUNT() FROM FlowDefinitionView WHERE IsActive = true];
    System.debug('active flows in org: ' + active + '  (exporter reads 200)');
    if (active > 200) {
        System.debug('SIGNAL: more active flows than one batch. The exporter '
            + 'now reads record-triggered ones first, but any beyond 200 of '
            + 'those are still unseen.');
    }
} catch (Exception e) {
    System.debug('COUNT() on FlowDefinitionView refused: ' + e.getMessage());
}

// Can the view be filtered to record-triggered flows at all? This is the
// filter the exporter relies on to stop screen flows eating the batch.
try {
    List<FlowDefinitionView> triggered = Database.query(
        'SELECT ApiName, TriggerObjectOrEventLabel FROM FlowDefinitionView '
        + 'WHERE IsActive = true AND TriggerObjectOrEventLabel != null '
        + 'ORDER BY ApiName LIMIT 200');
    System.debug('record-triggered flows readable in one filtered batch: '
        + triggered.size());
} catch (Exception e) {
    System.debug('SIGNAL: FlowDefinitionView will not filter or sort on '
        + 'TriggerObjectOrEventLabel here (' + e.getMessage() + '), so the '
        + 'exporter falls back to an arbitrary batch of 200.');
}

try {
    for (FlowDefinitionView f : [
            SELECT ApiName, Label, ProcessType, TriggerType,
                   TriggerObjectOrEventLabel, VersionNumber
            FROM FlowDefinitionView
            WHERE IsActive = true AND TriggerObjectOrEventLabel = 'Account'
            LIMIT 50]) {
        System.debug('ACCOUNT FLOW: ' + f.ApiName + ' | ' + f.Label
            + ' | ' + f.ProcessType + ' | ' + f.TriggerType);
    }
} catch (Exception e) {
    System.debug('could not filter flows by trigger object: ' + e.getMessage());
}

// ---- 4. what actually landed in the graph ---------------------------------
AIGraphDocument doc = AIGraphFileStore.load(AIGraphFileStore.COMBINED);
if (doc == null) {
    System.debug('no combined graph file; build the graph first');
} else {
    System.debug('graph: ' + doc.nodes.size() + ' nodes, '
        + doc.relationships.size() + ' edges');
    for (String note : doc.notes) {
        System.debug('note: ' + note);
    }
    Integer flowNodes = 0;
    Boolean accountNode = false;
    Boolean accountIsBoundary = false;
    for (AIGraphDocument.GraphNode n : doc.nodes) {
        if (n.nodeType == 'Flow') { flowNodes++; }
        if (n.id == 'sobj:Account') {
            accountNode = true;
            accountIsBoundary = n.properties != null
                && n.properties.contains('boundary');
        }
    }
    System.debug('Flow nodes in graph: ' + flowNodes
        + ' | sobj:Account node present: ' + accountNode
        + ' | present only as a boundary node: ' + accountIsBoundary);
    Integer accountEdges = 0;
    for (AIGraphDocument.GraphEdge e : doc.relationships) {
        if (e.toId == 'sobj:Account' && e.edgeType == 'FLOW_UPDATES_SOBJECT') {
            accountEdges++;
            System.debug('EDGE: ' + e.fromId + ' -> Account (' + e.origin + ')');
        }
    }
    System.debug('flow edges into Account: ' + accountEdges);
}

// ---- 5. is the cheap flow-internals route available? ----------------------
// If a flow's elements are readable with plain SOQL, what a flow CREATES can
// be known without the Tooling API, and P4 gets much smaller for this case.
Map<String, Schema.SObjectType> g = Schema.getGlobalDescribe();
System.debug('FlowVersionView available: ' + g.containsKey('FlowVersionView'));
System.debug('FlowElementView available: ' + g.containsKey('FlowElementView'));

// Availability is not usefulness. What matters is whether any field on
// FlowElementView names the object an element writes to.
if (g.containsKey('FlowElementView')) {
    try {
        for (String fieldName :
                g.get('FlowElementView').getDescribe().fields.getMap().keySet()) {
            System.debug('FlowElementView field: ' + fieldName);
        }
    } catch (Exception e) {
        System.debug('FlowElementView describe refused: ' + e.getMessage());
    }
    try {
        for (SObject row : Database.query(
                'SELECT FlowVersionViewId, ElementType, ElementSubtype, '
                + 'Name FROM FlowElementView LIMIT 5')) {
            System.debug('FlowElementView sample: ' + row);
        }
    } catch (Exception e) {
        System.debug('FlowElementView is not queryable here: ' + e.getMessage());
    }
}
