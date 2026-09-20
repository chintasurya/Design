/**
 * Clear the graph, then optionally rebuild.
 *
 * The builder upserts on external id, so narrowing the scope leaves every
 * previously written node in place: a first build over the whole org wrote
 * 36,330 nodes, and rebuilding over a pod would have added a few thousand
 * correct ones on top of 30,000 wrong ones. Stale data that looks like a
 * healthy graph is worse than no graph.
 *
 * Edges go first, then nodes, then the build, each chained from the previous
 * finish() because the volumes exceed a single transaction's DML limit.
 */
public with sharing class AIGraphPurge implements Database.Batchable<SObject>,
                                                 Database.Stateful {

    public enum Phase { EDGES, NODES }

    private Phase phase;
    private Boolean rebuildAfter;

    public AIGraphPurge(Phase startPhase, Boolean rebuildAfter) {
        this.phase = startPhase;
        this.rebuildAfter = rebuildAfter;
    }

    public static Id run(Boolean rebuildAfter) {
        return Database.executeBatch(new AIGraphPurge(Phase.EDGES, rebuildAfter), 2000);
    }

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return phase == Phase.EDGES
            ? Database.getQueryLocator('SELECT Id FROM Graph_Edge__c')
            : Database.getQueryLocator('SELECT Id FROM Graph_Node__c');
    }

    public void execute(Database.BatchableContext ctx, List<SObject> scope) {
        Database.delete(scope, false);
    }

    public void finish(Database.BatchableContext ctx) {
        if (phase == Phase.EDGES) {
            Database.executeBatch(new AIGraphPurge(Phase.NODES, rebuildAfter), 2000);
        } else if (rebuildAfter && !Test.isRunningTest()) {
            AIGraphBuilder.run();
        }
    }
}
