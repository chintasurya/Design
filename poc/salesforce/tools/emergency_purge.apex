// Developer Console > Debug > Open Execute Anonymous Window
// Run repeatedly until the debug log prints 0. Frees storage immediately.
List<Graph_Edge__c> edges = [SELECT Id FROM Graph_Edge__c LIMIT 9000];
if (!edges.isEmpty()) {
    delete edges;
    Database.emptyRecycleBin(edges);
}
List<Graph_Node__c> nodes =
    edges.isEmpty() ? [SELECT Id FROM Graph_Node__c LIMIT 9000]
                    : new List<Graph_Node__c>();
if (!nodes.isEmpty()) {
    delete nodes;
    Database.emptyRecycleBin(nodes);
}
System.debug('freed: ' + edges.size() + ' edges, ' + nodes.size() + ' nodes');
