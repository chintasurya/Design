/**
 * Builds the knowledge graph once, so queries can traverse it many times.
 *
 * This is the difference between a graph and a search. Search asks the org a
 * question every time. A graph resolves the relationships up front, persists
 * them as typed edges, and then answers by walking those edges. Multi-hop
 * blast radius only exists because the edges are already there.
 *
 * Six edge types come out of live Salesforce metadata with no callout:
 *
 *   SOBJECT_HAS_FIELD            describe() field map
 *   SOBJECT_HAS_RECORDTYPE       describe() record type infos
 *   SOBJECT_RELATES_TO_SOBJECT   lookup and master-detail referenceTo
 *   TRIGGER_FIRES_ON_SOBJECT     ApexTrigger.TableEnumOrId
 *   FLOW_UPDATES_SOBJECT         FlowDefinitionView trigger object
 *   APEX_REFERENCES_SOBJECT      ApexClass.Body scanned for API names
 *
 * Runs as a batch because describe() and body scanning are heavy, and the
 * whole point is that this cost is paid once per sync rather than per query.
 */
public with sharing class AIGraphBuilder implements Database.Batchable<String>,
                                                   Database.Stateful {

    public String snapshotId;
    public Integer nodeCount = 0;
    public Integer edgeCount = 0;

    private static final Integer SCOPE_SIZE = 8;
    private static final Integer MAX_FIELDS_PER_OBJECT = 250;

    public AIGraphBuilder() {
        snapshotId = String.valueOf(System.now().getTime());
    }

    public static Id run() {
        return Database.executeBatch(new AIGraphBuilder(), SCOPE_SIZE);
    }

    public Iterable<String> start(Database.BatchableContext ctx) {
        AINetworkServicesScope scope = AINetworkServicesScope.resolve(
            AIServiceFactory.config().Pod_Profile_Name__c);
        List<String> objects = new List<String>();
        Map<String, Schema.SObjectType> described = Schema.getGlobalDescribe();

        for (String apiName : described.keySet()) {
            if (!scope.covers(apiName)) {
                continue;
            }
            // Skip the platform noise no one is asking questions about.
            if (apiName.endsWith('__History') || apiName.endsWith('__Share')
                    || apiName.endsWith('__Feed') || apiName.endsWith('__Tag')
                    || apiName.endsWith('ChangeEvent')) {
                continue;
            }
            objects.add(apiName);
        }
        objects.sort();
        return objects;
    }

    public void execute(Database.BatchableContext ctx, List<String> objects) {
        Map<String, Graph_Node__c> nodes = new Map<String, Graph_Node__c>();
        Map<String, Graph_Edge__c> edges = new Map<String, Graph_Edge__c>();
        Map<String, Schema.SObjectType> described = Schema.getGlobalDescribe();

        for (String apiName : objects) {
            Schema.SObjectType sot = described.get(apiName);
            if (sot == null) {
                continue;
            }
            addObject(nodes, edges, sot, apiName);
        }
        commitGraph(nodes, edges);
    }

    /** Automation spans objects, so it is resolved once at the end. */
    public void finish(Database.BatchableContext ctx) {
        Map<String, Graph_Node__c> nodes = new Map<String, Graph_Node__c>();
        Map<String, Graph_Edge__c> edges = new Map<String, Graph_Edge__c>();

        Set<String> known = new Set<String>();
        for (Graph_Node__c n : [SELECT Api_Name__c FROM Graph_Node__c
                                WHERE Node_Type__c = 'SObject'
                                AND Snapshot_Id__c = :snapshotId LIMIT 5000]) {
            known.add(n.Api_Name__c);
        }

        addTriggers(nodes, edges, known);
        addFlows(nodes, edges, known);
        addApexClasses(nodes, edges, known);
        commitGraph(nodes, edges);
    }

    // ----------------------------------------------------------- object graph

    private void addObject(Map<String, Graph_Node__c> nodes,
                           Map<String, Graph_Edge__c> edges,
                           Schema.SObjectType sot, String apiName) {
        Schema.DescribeSObjectResult d = sot.getDescribe();
        Map<String, Schema.SObjectField> fields = d.fields.getMap();
        String objId = 'sobj:' + apiName;

        node(nodes, objId, 'SObject', d.getLabel(), apiName,
            '{"fieldCount":' + fields.size()
            + ',"custom":' + d.isCustom()
            + ',"queryable":' + d.isQueryable() + '}',
            fields.size() > 100 ? 'High' : 'Medium',
            'SCHEMA describe(' + apiName + ')');

        for (Schema.RecordTypeInfo rt : d.getRecordTypeInfos()) {
            if (rt.isMaster() || !rt.isAvailable()) {
                continue;
            }
            String rtId = 'rt:' + apiName + '.' + rt.getDeveloperName();
            node(nodes, rtId, 'RecordType', rt.getName(), rt.getDeveloperName(),
                '{"default":' + rt.isDefaultRecordTypeMapping() + '}', 'Low',
                'SCHEMA record type on ' + apiName);
            edge(edges, objId, rtId, 'SOBJECT_HAS_RECORDTYPE',
                'describe().getRecordTypeInfos()');
        }

        Integer n = 0;
        for (String fieldName : fields.keySet()) {
            if (n++ >= MAX_FIELDS_PER_OBJECT) {
                break;
            }
            Schema.DescribeFieldResult fd = fields.get(fieldName).getDescribe();
            String fieldId = 'field:' + apiName + '.' + fd.getName();

            node(nodes, fieldId, 'Field', fd.getLabel(), fd.getName(),
                '{"type":"' + fd.getType() + '"'
                + ',"custom":' + fd.isCustom()
                + ',"formula":' + fd.isCalculated()
                + ',"required":' + (!fd.isNillable()) + '}',
                fd.isCalculated() ? 'High' : 'Low',
                'SCHEMA ' + apiName + '.' + fd.getName() + ' · ' + fd.getType());
            edge(edges, objId, fieldId, 'SOBJECT_HAS_FIELD',
                'describe().fields.getMap()');

            // A lookup is a real relationship between two objects.
            if (fd.getType() == Schema.DisplayType.REFERENCE) {
                for (Schema.SObjectType ref : fd.getReferenceTo()) {
                    String target = ref.getDescribe().getName();
                    edge(edges, objId, 'sobj:' + target,
                        'SOBJECT_RELATES_TO_SOBJECT',
                        'via ' + fd.getName() + ' · '
                        + (fd.getRelationshipOrder() == null
                           ? 'lookup' : 'master-detail'));
                }
            }
        }
    }

    // -------------------------------------------------------------- automation

    private void addTriggers(Map<String, Graph_Node__c> nodes,
                             Map<String, Graph_Edge__c> edges, Set<String> known) {
        List<ApexTrigger> triggers = [
            SELECT Name, TableEnumOrId, Status, ApiVersion
            FROM ApexTrigger WHERE NamespacePrefix = null LIMIT 200];
        for (ApexTrigger t : triggers) {
            if (!known.contains(t.TableEnumOrId)) {
                continue;
            }
            String id = 'trigger:' + t.Name;
            node(nodes, id, 'ApexTrigger', t.Name, t.Name,
                '{"status":"' + t.Status + '","apiVersion":' + t.ApiVersion + '}',
                'High', 'METADATA ApexTrigger on ' + t.TableEnumOrId);
            edge(edges, id, 'sobj:' + t.TableEnumOrId, 'TRIGGER_FIRES_ON_SOBJECT',
                'ApexTrigger.TableEnumOrId');
        }
    }

    private void addFlows(Map<String, Graph_Node__c> nodes,
                          Map<String, Graph_Edge__c> edges, Set<String> known) {
        // FlowDefinitionView rejects queryMore(), so this must be a single batch.
        List<FlowDefinitionView> flows = [
            SELECT ApiName, Label, ProcessType, TriggerType,
                   TriggerObjectOrEventLabel, VersionNumber
            FROM FlowDefinitionView WHERE IsActive = true LIMIT 200];
        for (FlowDefinitionView f : flows) {
            String id = 'flow:' + f.ApiName;
            node(nodes, id, 'Flow', f.Label, f.ApiName,
                '{"processType":"' + f.ProcessType + '","version":'
                + f.VersionNumber + '}', 'High',
                'METADATA Flow ' + f.ApiName + ' v' + f.VersionNumber);
            if (String.isNotBlank(f.TriggerObjectOrEventLabel)
                    && known.contains(f.TriggerObjectOrEventLabel)) {
                edge(edges, id, 'sobj:' + f.TriggerObjectOrEventLabel,
                    'FLOW_UPDATES_SOBJECT', 'record-triggered flow');
            }
        }
    }

    /**
     * Scan class bodies for object API names. Crude next to a real parser, but
     * it produces genuine APEX_REFERENCES_SOBJECT edges from the source itself
     * rather than from a name resembling another name.
     */
    private void addApexClasses(Map<String, Graph_Node__c> nodes,
                                Map<String, Graph_Edge__c> edges, Set<String> known) {
        List<ApexClass> classes = [
            SELECT Name, Body, ApiVersion, LengthWithoutComments
            FROM ApexClass
            WHERE NamespacePrefix = null AND LengthWithoutComments < 40000
            ORDER BY Name LIMIT 150];

        for (ApexClass c : classes) {
            Boolean isTest = c.Body != null && c.Body.containsIgnoreCase('@isTest');
            String id = 'apex:' + c.Name;
            node(nodes, id, isTest ? 'TestClass' : 'ApexClass', c.Name, c.Name,
                '{"apiVersion":' + c.ApiVersion + ',"length":'
                + c.LengthWithoutComments + ',"test":' + isTest + '}',
                c.LengthWithoutComments > 5000 ? 'High' : 'Medium',
                'METADATA ApexClass ' + c.Name);

            if (c.Body == null) {
                continue;
            }
            for (String apiName : known) {
                if (c.Body.contains(apiName)) {
                    edge(edges, id, 'sobj:' + apiName, 'APEX_REFERENCES_SOBJECT',
                        'API name found in ApexClass.Body');
                }
            }
            c.Body = null;   // release heap before the next class
        }
    }

    // ------------------------------------------------------------- persistence

    private void node(Map<String, Graph_Node__c> nodes, String nodeId, String nodeType,
                      String name, String apiName, String props, String risk,
                      String provenance) {
        if (nodes.containsKey(nodeId)) {
            return;
        }
        nodes.put(nodeId, new Graph_Node__c(
            Node_Id__c = nodeId,
            Node_Type__c = nodeType,
            Node_Name__c = trim(name, 255),
            Api_Name__c = trim(apiName, 255),
            Properties__c = props,
            Source_System__c = 'Salesforce',
            Provenance__c = provenance,
            Risk_Tier__c = risk,
            Snapshot_Id__c = snapshotId));
    }

    private void edge(Map<String, Graph_Edge__c> edges, String fromId, String toId,
                      String edgeType, String provenance) {
        String edgeId = fromId + '|' + edgeType + '|' + toId;
        if (edges.containsKey(edgeId)) {
            return;
        }
        edges.put(edgeId, new Graph_Edge__c(
            Edge_Id__c = trim(edgeId, 255),
            From_Node_Id__c = trim(fromId, 255),
            To_Node_Id__c = trim(toId, 255),
            Edge_Type__c = edgeType,
            Origin__c = 'FACTUAL',
            Confidence__c = 1.0,
            Provenance__c = provenance,
            Snapshot_Id__c = snapshotId));
    }

    private void commitGraph(Map<String, Graph_Node__c> nodes,
                             Map<String, Graph_Edge__c> edges) {
        if (!nodes.isEmpty()) {
            Database.upsert(nodes.values(), Graph_Node__c.Node_Id__c, false);
            nodeCount += nodes.size();
        }
        if (!edges.isEmpty()) {
            Database.upsert(edges.values(), Graph_Edge__c.Edge_Id__c, false);
            edgeCount += edges.size();
        }
    }

    private static String trim(String value, Integer max) {
        if (value == null) {
            return null;
        }
        return value.length() > max ? value.substring(0, max) : value;
    }
}
