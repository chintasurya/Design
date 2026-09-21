/*
 * Rebuild the knowledge graph, then check the job finished.
 *
 * Paste into Developer Console > Debug > Open Execute Anonymous Window, tick
 * "Open Log", run. This one WRITES: it enqueues the export, which replaces
 * the graph file. It does not touch any org data — the graph lives in a
 * Salesforce File (ContentVersion), never in records.
 *
 * Run this after every deploy that changes the pod definition, the exporter
 * or the scope rules. A graph built before those changes answers questions
 * about an org that no longer matches the code reading it.
 *
 * Two steps, and they are deliberately separate runs:
 *   1. enqueue      returns immediately, the work happens asynchronously
 *   2. check        run it again 30 to 60 seconds later
 */

// ---- 1. enqueue -----------------------------------------------------------
// Comment this line out on the second run, or a second export is queued on
// top of the first.
System.debug('enqueued job: ' + AIGraphSalesforceExport.start());

// ---- 2. check -------------------------------------------------------------
// Meaningless on the first run, since the job has not started. Run the whole
// script again after half a minute and read these lines.
for (AsyncApexJob j : [
        SELECT Status, ExtendedStatus, NumberOfErrors, JobItemsProcessed,
               TotalJobItems, CreatedDate, CompletedDate
        FROM AsyncApexJob
        WHERE ApexClass.Name = 'AIGraphSalesforceExport'
        ORDER BY CreatedDate DESC LIMIT 3]) {
    System.debug(j.CreatedDate + ' · ' + j.Status
        + ' · errors ' + j.NumberOfErrors
        + ' · ' + (j.ExtendedStatus == null ? 'no message' : j.ExtendedStatus));
}

// ---- 3. what landed -------------------------------------------------------
AIGraphDocument doc = AIGraphFileStore.load(AIGraphFileStore.COMBINED);
if (doc == null) {
    System.debug('No graph file yet. Either the job has not finished, or it '
        + 'failed — read the Status and message above.');
} else {
    System.debug('graph: ' + doc.nodes.size() + ' nodes · '
        + doc.relationships.size() + ' edges · exported ' + doc.exportedAt);
    // The notes carry the scope, the object list, what was truncated and what
    // could not be resolved. They are the export explaining itself.
    for (String note : doc.notes) {
        System.debug('note: ' + note);
    }
    Map<String, Integer> byType = new Map<String, Integer>();
    for (AIGraphDocument.GraphNode n : doc.nodes) {
        Integer c = byType.containsKey(n.nodeType) ? byType.get(n.nodeType) : 0;
        byType.put(n.nodeType, c + 1);
    }
    System.debug('nodes by type: ' + byType);
    Map<String, Integer> byEdge = new Map<String, Integer>();
    for (AIGraphDocument.GraphEdge e : doc.relationships) {
        Integer c = byEdge.containsKey(e.edgeType) ? byEdge.get(e.edgeType) : 0;
        byEdge.put(e.edgeType, c + 1);
    }
    System.debug('edges by type: ' + byEdge);
}

/*
 * If the job Status is Failed with ScopeTooWideException, the declared pod
 * plus the profile-writable objects plus the record-type objects came to more
 * than the 220 the export allows. Send the message: the fix is in the code,
 * not in the org.
 */
