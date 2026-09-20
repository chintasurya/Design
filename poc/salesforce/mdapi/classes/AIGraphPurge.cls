/**
 * Clear the graph, then optionally rebuild.
 *
 * The builder upserts on external id, so narrowing the scope leaves every
 * previously written node in place: a first build over the whole org wrote
 * 36,330 nodes and 76,980 edges, about 221 MB of data storage, and rebuilding
 * over a pod would have added a few thousand correct rows on top of thirty
 * thousand wrong ones. Stale data that looks like a healthy graph is worse
 * than no graph.
 *
 * Edges first, then nodes, then the build, each chained from the previous
 * finish() because the volumes exceed one transaction's DML limit.
 *
 * Phase is a String rather than an enum on purpose. An inner enum referenced
 * unqualified inside its own class fails to compile with "Static field cannot
 * be referenced from a non static context", which is an Apex resolution quirk
 * rather than anything wrong with the code. Two constants sidestep it.
 */
public with sharing class AIGraphPurge implements Database.Batchable<SObject>,
                                                 Database.Stateful {

    @TestVisible private static final String EDGES = 'edges';
    @TestVisible private static final String NODES = 'nodes';

    private String phase;
    private Boolean rebuildAfter;

    public AIGraphPurge(String phase, Boolean rebuildAfter) {
        this.phase = phase;
        this.rebuildAfter = rebuildAfter;
    }

    public static Id run(Boolean rebuildAfter) {
        return Database.executeBatch(new AIGraphPurge(EDGES, rebuildAfter), 2000);
    }

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return EDGES.equals(phase)
            ? Database.getQueryLocator('SELECT Id FROM Graph_Edge__c')
            : Database.getQueryLocator('SELECT Id FROM Graph_Node__c');
    }

    public void execute(Database.BatchableContext ctx, List<SObject> scope) {
        Database.delete(scope, false);
        // A plain delete frees no storage: rows sit in the Recycle Bin for 15
        // days and still count. emptyRecycleBin draws on the SAME 10,000 DML
        // row governor as the delete, which is why the scope size is 2,000.
        Database.emptyRecycleBin(scope);
    }

    public void finish(Database.BatchableContext ctx) {
        if (EDGES.equals(phase)) {
            Database.executeBatch(new AIGraphPurge(NODES, rebuildAfter), 2000);
        } else if (rebuildAfter && !Test.isRunningTest()) {
            AIGraphBuilder.run();
        }
    }
}
