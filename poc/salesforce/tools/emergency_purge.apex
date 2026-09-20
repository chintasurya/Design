// Developer Console > Debug > Open Execute Anonymous Window.
// Run repeatedly until the log prints 0.
//
// LIMIT is 4000, not 9000: emptyRecycleBin() counts against the SAME 10,000
// DML row governor as the delete itself, so each pass costs 2x the limit.
// 4000 + 4000 = 8000, comfortably under.
//
// Faster alternative once the latest package is deployed, one line, no repeats:
//     AIGraphPurge.run(false);

List<Graph_Edge__c> edges = [SELECT Id FROM Graph_Edge__c LIMIT 4000];
if (!edges.isEmpty()) {
    delete edges;
    Database.emptyRecycleBin(edges);
}

List<Graph_Node__c> nodes =
    edges.isEmpty() ? [SELECT Id FROM Graph_Node__c LIMIT 4000]
                    : new List<Graph_Node__c>();
if (!nodes.isEmpty()) {
    delete nodes;
    Database.emptyRecycleBin(nodes);
}

System.debug(LoggingLevel.ERROR,
    'freed ' + edges.size() + ' edges, ' + nodes.size() + ' nodes');
