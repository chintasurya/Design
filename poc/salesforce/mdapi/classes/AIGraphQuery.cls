/**
 * Traversal over the persisted graph.
 *
 * One indexed SOQL per hop, regardless of graph size, because
 * Graph_Edge__c.From_Node_Id__c is an external id and therefore indexed. Three
 * hops is three queries against a limit of 100. That is the property that
 * makes a graph answer reachability questions a search cannot: cost scales
 * with what is connected, not with how much exists.
 */
public with sharing class AIGraphQuery {

    public class Hit {
        public Graph_Node__c node;
        public Integer hops;
        public String path;
        public String viaEdgeType;
    }

    public static Boolean isBuilt() {
        return [SELECT COUNT() FROM Graph_Node__c LIMIT 1] > 0;
    }

    public static Integer nodeCount() {
        return [SELECT COUNT() FROM Graph_Node__c];
    }

    public static Integer edgeCount() {
        return [SELECT COUNT() FROM Graph_Edge__c];
    }

    /** Nodes whose name or api name contains any term. The traversal seeds. */
    public static List<Graph_Node__c> seeds(Set<String> terms, String preferredType,
                                            Integer maxSeeds) {
        List<Graph_Node__c> out = new List<Graph_Node__c>();
        if (terms.isEmpty()) {
            return out;
        }
        Set<Id> seen = new Set<Id>();
        for (String term : terms) {
            String like = '%' + term + '%';
            for (Graph_Node__c n : [
                    SELECT Id, Node_Id__c, Node_Type__c, Node_Name__c, Api_Name__c,
                           Properties__c, Provenance__c, Risk_Tier__c, Source_System__c
                    FROM Graph_Node__c
                    WHERE Api_Name__c LIKE :like OR Node_Name__c LIKE :like
                    ORDER BY Node_Type__c
                    LIMIT 40]) {
                if (seen.add(n.Id)) {
                    out.add(n);
                }
            }
            if (out.size() >= maxSeeds * 4) {
                break;
            }
        }
        // An explicitly requested type sorts first.
        if (String.isNotBlank(preferredType) && preferredType != 'Unknown') {
            List<Graph_Node__c> preferred = new List<Graph_Node__c>();
            List<Graph_Node__c> rest = new List<Graph_Node__c>();
            for (Graph_Node__c n : out) {
                if (n.Node_Type__c == preferredType) {
                    preferred.add(n);
                } else {
                    rest.add(n);
                }
            }
            preferred.addAll(rest);
            out = preferred;
        }
        return out.size() > maxSeeds
            ? new List<Graph_Node__c>(subList(out, maxSeeds)) : out;
    }

    /**
     * Everything reachable from the seeds within maxHops, in both directions.
     * Direction matters: a Flow points at the object it updates, so the
     * question "what touches this object" has to walk incoming edges too.
     */
    public static List<Hit> blastRadius(List<String> seedNodeIds, Integer maxHops,
                                        Integer maxNodes) {
        List<Hit> hits = new List<Hit>();
        if (seedNodeIds == null || seedNodeIds.isEmpty()) {
            return hits;
        }
        Set<String> visited = new Set<String>(seedNodeIds);
        Set<String> frontier = new Set<String>(seedNodeIds);
        Map<String, String> pathOf = new Map<String, String>();
        Map<String, String> edgeOf = new Map<String, String>();
        Map<String, Integer> hopOf = new Map<String, Integer>();
        for (String s : seedNodeIds) {
            hopOf.put(s, 0);
        }

        for (Integer hop = 1; hop <= maxHops && !frontier.isEmpty(); hop++) {
            // One query per hop, out and back, over an indexed field.
            List<Graph_Edge__c> edges = [
                SELECT From_Node_Id__c, To_Node_Id__c, Edge_Type__c, Provenance__c
                FROM Graph_Edge__c
                WHERE From_Node_Id__c IN :frontier OR To_Node_Id__c IN :frontier
                LIMIT 2000];

            Set<String> next = new Set<String>();
            for (Graph_Edge__c e : edges) {
                String other;
                String direction;
                if (frontier.contains(e.From_Node_Id__c)
                        && !visited.contains(e.To_Node_Id__c)) {
                    other = e.To_Node_Id__c;
                    direction = e.From_Node_Id__c + ' -[' + e.Edge_Type__c + ']-> ';
                } else if (frontier.contains(e.To_Node_Id__c)
                        && !visited.contains(e.From_Node_Id__c)) {
                    other = e.From_Node_Id__c;
                    direction = e.From_Node_Id__c + ' -[' + e.Edge_Type__c + ']-> ';
                } else {
                    continue;
                }
                if (visited.add(other)) {
                    next.add(other);
                    hopOf.put(other, hop);
                    pathOf.put(other, direction + other);
                    edgeOf.put(other, e.Edge_Type__c);
                }
                if (visited.size() >= maxNodes) {
                    break;
                }
            }
            if (visited.size() >= maxNodes) {
                break;
            }
            frontier = next;
        }

        for (Graph_Node__c n : [
                SELECT Id, Node_Id__c, Node_Type__c, Node_Name__c, Api_Name__c,
                       Properties__c, Provenance__c, Risk_Tier__c, Source_System__c
                FROM Graph_Node__c
                WHERE Node_Id__c IN :visited
                LIMIT 500]) {
            Hit h = new Hit();
            h.node = n;
            h.hops = hopOf.containsKey(n.Node_Id__c) ? hopOf.get(n.Node_Id__c) : 0;
            h.path = pathOf.containsKey(n.Node_Id__c)
                   ? pathOf.get(n.Node_Id__c) : 'Matched the request directly';
            h.viaEdgeType = edgeOf.get(n.Node_Id__c);
            hits.add(h);
        }
        return hits;
    }

    private static List<Graph_Node__c> subList(List<Graph_Node__c> source, Integer size) {
        List<Graph_Node__c> out = new List<Graph_Node__c>();
        for (Integer i = 0; i < size && i < source.size(); i++) {
            out.add(source[i]);
        }
        return out;
    }
}
