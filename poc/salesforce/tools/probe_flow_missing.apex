/*
 * Why is no Flow linked to Account?
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run, then read the USER_DEBUG lines. Read-only: it queries and
 * prints, it writes nothing to the org.
 *
 * It answers four questions in order, cheapest first, because three of the
 * four possible causes need no Tooling API at all:
 *   1. is Account inside the Network Services scope?
 *   2. does FlowDefinitionView even report a record-triggered flow on Account?
 *   3. did the 200-flow cap cut it off?
 *   4. did it reach the graph file?
 */

String POD = 'Network Services';

// ---- 1. scope -------------------------------------------------------------
AINetworkServicesScope scope = AINetworkServicesScope.resolve(POD);
System.debug('profile matched: ' + scope.matchedProfile
    + ' (found=' + scope.profileFound + ')');
System.debug('scope size: ' + scope.owned.size()
    + ' owned, ' + scope.writable.size() + ' writable, '
    + scope.readable.size() + ' readable');
System.debug('Account in scope: ' + scope.covers('Account'));
System.debug('HealthcareProvider in scope: ' + scope.covers('HealthcareProvider'));
System.debug('HealthcareFacility in scope: ' + scope.covers('HealthcareFacility'));

// ---- 2 and 3. what FlowDefinitionView reports -----------------------------
// No LIMIT here and no cap: this is the honest total, to compare against the
// 200 the exporter takes.
Integer active = [SELECT COUNT() FROM FlowDefinitionView WHERE IsActive = true];
System.debug('active flows in org: ' + active + '  (exporter reads 200)');

for (FlowDefinitionView f : [
        SELECT ApiName, Label, ProcessType, TriggerType,
               TriggerObjectOrEventLabel, VersionNumber
        FROM FlowDefinitionView
        WHERE IsActive = true AND TriggerObjectOrEventLabel = 'Account'
        LIMIT 50]) {
    System.debug('ACCOUNT FLOW: ' + f.ApiName + ' | ' + f.Label
        + ' | ' + f.ProcessType + ' | ' + f.TriggerType);
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
    for (AIGraphDocument.GraphNode n : doc.nodes) {
        if (n.nodeType == 'Flow') { flowNodes++; }
        if (n.id == 'sobj:Account') { accountNode = true; }
    }
    System.debug('Flow nodes in graph: ' + flowNodes
        + ' | sobj:Account node present: ' + accountNode);
    for (AIGraphDocument.GraphEdge e : doc.relationships) {
        if (e.toId == 'sobj:Account' && e.edgeType == 'FLOW_UPDATES_SOBJECT') {
            System.debug('EDGE: ' + e.fromId + ' -> Account (' + e.origin + ')');
        }
    }
}

// ---- bonus: is the cheap flow-internals route available? ------------------
// If FlowElementView is describable, what a flow CREATES may be readable with
// plain SOQL, and the Tooling API setup can be skipped for this case.
Map<String, Schema.SObjectType> g = Schema.getGlobalDescribe();
System.debug('FlowVersionView available: ' + g.containsKey('FlowVersionView'));
System.debug('FlowElementView available: ' + g.containsKey('FlowElementView'));
