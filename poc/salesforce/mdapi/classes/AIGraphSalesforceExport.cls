/**
 * Layers 2, 3 and 6 for the Salesforce source: read it, interpret it, export
 * the neutral graph document.
 *
 * A Queueable, not a Batch. Batch state has to survive serialization between
 * chunks, and a growing node list does not do that well. One asynchronous
 * transaction gives 60s CPU and 12 MB heap, which comfortably covers a pod of
 * up to a couple of hundred objects.
 *
 * The scope guard is the important part. The previous record-based builder
 * silently walked ~1,400 objects and wrote 221 MB, filling the sandbox. This
 * one refuses to start when the scope looks like a whole org, because a
 * failure that names the cause beats a success that quietly produces garbage.
 */
public with sharing class AIGraphSalesforceExport implements Queueable {

    /** Above this, the scope is not a pod and the JSON would not load anyway. */
    @TestVisible private static final Integer MAX_OBJECTS = 220;
    private static final Integer MAX_FIELDS_PER_OBJECT = 200;

    /**
     * One batch, because FlowDefinitionView rejects queryMore() and cannot be
     * paged at all. The cap is not the interesting number; WHICH 200 rows come
     * back is, which is why the read asks for record-triggered flows first.
     */
    private static final Integer MAX_FLOWS = 200;

    /**
     * Objects pulled in from outside the pod purely because automation inside
     * the pod fires on them. One node each, no fields, no record types. The
     * cap exists only so a pathological org cannot unbound the graph.
     */
    private static final Integer MAX_BOUNDARY_OBJECTS = 150;

    public class ScopeTooWideException extends Exception {}

    public void execute(QueueableContext ctx) {
        build();
    }

    public static Id start() {
        return System.enqueueJob(new AIGraphSalesforceExport());
    }

    public static AIGraphDocument build() {
        AINetworkServicesScope scope = AINetworkServicesScope.resolve(
            AIServiceFactory.config().Pod_Profile_Name__c);

        List<String> targets = inScopeObjects(scope);
        if (targets.isEmpty()) {
            // 350 orphan nodes and zero edges is what an empty scope looks
            // like when the export carries on regardless. Refuse instead.
            throw new ScopeTooWideException(
                'No objects are in scope, so there is nothing to build a graph '
                + 'from. ' + scope.note);
        }
        if (targets.size() > MAX_OBJECTS) {
            throw new ScopeTooWideException(
                'Scope resolved to ' + targets.size() + ' objects, over the '
                + MAX_OBJECTS + ' limit. That is an org, not a pod: the export '
                + 'would exceed the heap ceiling when loaded. ' + scope.note);
        }

        AIGraphDocument doc = new AIGraphDocument();
        doc.source = 'SALESFORCE';
        doc.snapshotId = String.valueOf(System.now().getTime());
        doc.notes.add(scope.note);

        doc.notes.add(targets.size() + ' objects in scope');
        Map<String, Schema.SObjectType> described = Schema.getGlobalDescribe();
        Map<String, String> labelToApi = new Map<String, String>();
        Set<String> known = new Set<String>(targets);

        for (String apiName : targets) {
            addObject(doc, described.get(apiName), apiName, labelToApi);
        }

        // Automation is allowed to reach outside the pod. A Flow that is
        // record-triggered on Account is part of the pod's behaviour even when
        // Account itself is not a pod object, and dropping it was how the
        // console came to report "no automation fires on Account" while a Flow
        // on Account was doing exactly what the request asked for.
        Map<String, String> orgByName = orgIndex();
        Set<String> boundaryIds = new Set<String>();

        addTriggers(doc, known, labelToApi, orgByName, boundaryIds);
        addFlows(doc, known, labelToApi, orgByName, boundaryIds);
        addApexClasses(doc, known);

        if (!boundaryIds.isEmpty()) {
            doc.notes.add(boundaryIds.size() + ' object'
                + (boundaryIds.size() == 1 ? '' : 's')
                + ' outside the pod scope kept as boundary nodes because pod '
                + 'automation fires on them: '
                + String.join(new List<String>(boundaryIds), ', '));
        }

        doc.notes.add('Lightning components, validation rules and real '
            + 'dependency edges need the Tooling API, which is not configured');
        AIGraphFileStore.save(AIGraphFileStore.SALESFORCE, doc);
        rebuildCombined();
        return doc;
    }

    /** Re-merge whatever per-source files exist into the file queries read. */
    public static AIGraphDocument rebuildCombined() {
        List<AIGraphDocument> parts = new List<AIGraphDocument>();
        for (String name : new List<String>{
                AIGraphFileStore.SALESFORCE, AIGraphFileStore.JIRA,
                AIGraphFileStore.CONFLUENCE}) {
            AIGraphDocument part = AIGraphFileStore.load(name);
            if (part != null) {
                parts.add(part);
            }
        }
        AIGraphDocument combined = AIGraphDocument.combine(parts);
        AIGraphFileStore.save(AIGraphFileStore.COMBINED, combined);
        return combined;
    }

    // ------------------------------------------------------------------ scope

    private static List<String> inScopeObjects(AINetworkServicesScope scope) {
        List<String> targets = new List<String>();
        for (String apiName : Schema.getGlobalDescribe().keySet()) {
            if (!scope.covers(apiName)) {
                continue;
            }
            if (apiName.endsWith('__History') || apiName.endsWith('__Share')
                    || apiName.endsWith('__Feed') || apiName.endsWith('__Tag')
                    || apiName.endsWith('ChangeEvent')) {
                continue;
            }
            targets.add(apiName);
        }
        targets.sort();
        return targets;
    }

    // ----------------------------------------------------------------- nodes

    private static void addObject(AIGraphDocument doc, Schema.SObjectType sot,
                                  String apiName, Map<String, String> labelToApi) {
        if (sot == null) {
            return;
        }
        Schema.DescribeSObjectResult d = sot.getDescribe();
        Map<String, Schema.SObjectField> fields = d.fields.getMap();
        String objId = 'sobj:' + apiName;

        labelToApi.put(normalize(d.getLabel()), apiName);
        labelToApi.put(normalize(apiName), apiName);

        doc.addNode(objId, 'SObject', d.getLabel(), apiName,
            '{"fieldCount":' + fields.size() + ',"custom":' + d.isCustom() + '}',
            fields.size() > 100 ? 'High' : 'Medium',
            'SCHEMA describe(' + apiName + ') · ' + fields.size() + ' fields',
            'Salesforce');

        for (Schema.RecordTypeInfo rt : d.getRecordTypeInfos()) {
            if (rt.isMaster() || !rt.isAvailable()) {
                continue;
            }
            String rtId = 'rt:' + apiName + '.' + rt.getDeveloperName();
            doc.addNode(rtId, 'RecordType', rt.getName(), rt.getDeveloperName(),
                '{"default":' + rt.isDefaultRecordTypeMapping() + '}', 'Low',
                'SCHEMA record type on ' + apiName, 'Salesforce');
            doc.addEdge(objId, 'SOBJECT_HAS_RECORDTYPE', rtId,
                'describe().getRecordTypeInfos()');
        }

        Integer n = 0;
        for (String fieldName : fields.keySet()) {
            if (n++ >= MAX_FIELDS_PER_OBJECT) {
                doc.notes.add('Fields truncated at ' + MAX_FIELDS_PER_OBJECT
                    + ' for ' + apiName);
                break;
            }
            Schema.DescribeFieldResult fd = fields.get(fieldName).getDescribe();
            String fieldId = 'field:' + apiName + '.' + fd.getName();
            // Only non-default flags are written. Spelling out custom:false,
            // formula:false and required:false on every field cost roughly
            // 50 bytes each across a couple of thousand fields.
            String props = '{"dataType":"' + fd.getType() + '"';
            if (fd.isCustom()) {
                props += ',"custom":true';
            }
            if (fd.isCalculated()) {
                props += ',"formula":true';
            }
            if (!fd.isNillable()) {
                props += ',"required":true';
            }
            props += '}';
            doc.addNode(fieldId, 'Field', fd.getLabel(), fd.getName(), props,
                fd.isCalculated() ? 'High' : 'Low',
                'SCHEMA field · ' + fd.getType(),   // the id already names the object
                'Salesforce');
            doc.addEdge(objId, 'SOBJECT_HAS_FIELD', fieldId,
                'describe().fields.getMap()');

            if (fd.getType() == Schema.DisplayType.REFERENCE) {
                for (Schema.SObjectType ref : fd.getReferenceTo()) {
                    doc.addEdge(objId, 'SOBJECT_RELATES_TO_SOBJECT',
                        'sobj:' + ref.getDescribe().getName(),
                        'via ' + fd.getName());
                }
            }
        }
    }

    private static void addTriggers(AIGraphDocument doc, Set<String> known,
                                    Map<String, String> labelToApi,
                                    Map<String, String> orgByName,
                                    Set<String> boundaryIds) {
        List<ApexTrigger> triggers = [
            SELECT Name, TableEnumOrId, Status, ApiVersion
            FROM ApexTrigger WHERE NamespacePrefix = null LIMIT 200];
        for (ApexTrigger t : triggers) {
            String onObject = resolveAnywhere(
                t.TableEnumOrId, known, labelToApi, orgByName);
            if (onObject == null) {
                continue;
            }
            if (!known.contains(onObject)
                    && !addBoundaryObject(doc, onObject, boundaryIds)) {
                continue;
            }
            String id = 'trigger:' + t.Name;
            doc.addNode(id, 'ApexTrigger', t.Name, t.Name,
                '{"status":"' + t.Status + '"}', 'High',
                'METADATA ApexTrigger on ' + onObject, 'Salesforce');
            doc.addEdge(id, 'TRIGGER_FIRES_ON_SOBJECT', 'sobj:' + onObject,
                'ApexTrigger.TableEnumOrId');
        }
    }

    private static void addFlows(AIGraphDocument doc, Set<String> known,
                                 Map<String, String> labelToApi,
                                 Map<String, String> orgByName,
                                 Set<String> boundaryIds) {
        FlowRead read = readFlows(doc);
        List<FlowDefinitionView> flows = read.rows;

        Integer linked = 0;
        Integer outsidePod = 0;
        Integer noTrigger = 0;
        Integer unresolved = 0;

        for (FlowDefinitionView f : flows) {
            if (String.isBlank(f.TriggerObjectOrEventLabel)) {
                noTrigger++;       // screen or scheduled: no object to point at
                continue;
            }
            // TriggerObjectOrEventLabel is a LABEL, so it resolves through the
            // label map first and the whole-org index second. Comparing it to
            // API names alone matched only Account.
            String target = resolveAnywhere(
                f.TriggerObjectOrEventLabel, known, labelToApi, orgByName);
            if (target == null) {
                unresolved++;
                continue;
            }
            Boolean inPod = known.contains(target);
            if (!inPod && !addBoundaryObject(doc, target, boundaryIds)) {
                unresolved++;      // boundary budget spent
                continue;
            }
            String id = 'flow:' + f.ApiName;
            doc.addNode(id, 'Flow', f.Label, f.ApiName,
                '{"processType":"' + f.ProcessType + '","version":'
                    + f.VersionNumber + '}', 'High',
                'METADATA Flow ' + f.ApiName + ' v' + f.VersionNumber,
                'Salesforce');
            doc.addEdge(id, 'FLOW_UPDATES_SOBJECT', 'sobj:' + target,
                'record-triggered on ' + f.TriggerObjectOrEventLabel);
            linked++;
            if (!inPod) {
                outsidePod++;
            }
        }

        doc.notes.add(linked + ' of ' + flows.size() + ' active flows read are '
            + 'record-triggered on an object the graph can name'
            + (outsidePod == 0 ? '' : ' (' + outsidePod
                + ' on objects outside the pod, kept as boundary nodes)')
            + '; ' + unresolved + ' name something that could not be resolved '
            + 'to an object'
            + (read.triggeredOnly
                ? '. Flows with no trigger object were excluded by the query, '
                  + 'so they did not consume the batch'
                : ', ' + noTrigger + ' have no trigger object and are omitted '
                  + 'as unreachable'));
        if (flows.size() >= MAX_FLOWS) {
            doc.notes.add('The flow read filled its ' + MAX_FLOWS + '-row batch. '
                + 'FlowDefinitionView rejects queryMore(), so flows beyond that '
                + 'were not seen and any of them could hold automation this '
                + 'graph does not know about');
        }
    }

    /**
     * Active flows, the ones that can actually produce an edge first.
     *
     * The cap cannot be raised: FlowDefinitionView rejects queryMore(), so one
     * batch is all there is. That makes the ORDER of the read the thing that
     * matters. An unfiltered read with no ORDER BY returned an arbitrary 200,
     * and screen flows that can never yield an edge displaced record-triggered
     * flows that would have, which is one of the three candidate causes of a
     * Flow on Account never reaching the graph.
     *
     * The filter is dynamic deliberately. If TriggerObjectOrEventLabel is not
     * filterable or sortable in this org, a static query would fail to compile
     * and take the whole class with it; a dynamic one throws a QueryException
     * that can be caught, noted, and fallen back from.
     */
    private class FlowRead {
        private List<FlowDefinitionView> rows;
        private Boolean triggeredOnly = false;
    }

    private static FlowRead readFlows(AIGraphDocument doc) {
        FlowRead read = new FlowRead();
        String cols = 'ApiName, Label, ProcessType, TriggerType, '
                    + 'TriggerObjectOrEventLabel, VersionNumber';
        try {
            read.rows = (List<FlowDefinitionView>) Database.query(
                'SELECT ' + cols + ' FROM FlowDefinitionView '
                + 'WHERE IsActive = true AND TriggerObjectOrEventLabel != null '
                + 'ORDER BY ApiName LIMIT ' + MAX_FLOWS);
            read.triggeredOnly = true;
            return read;
        } catch (Exception e) {
            doc.notes.add('Flows could not be read record-triggered-first ('
                + e.getMessage() + '), so an arbitrary batch was read instead '
                + 'and a record-triggered flow may have been displaced');
        }
        // FlowDefinitionView rejects queryMore(), so this must be a list
        // assignment with an explicit LIMIT, never a SOQL for-loop.
        read.rows = [
            SELECT ApiName, Label, ProcessType, TriggerType,
                   TriggerObjectOrEventLabel, VersionNumber
            FROM FlowDefinitionView
            WHERE IsActive = true LIMIT :MAX_FLOWS];
        return read;
    }

    private static void addApexClasses(AIGraphDocument doc, Set<String> known) {
        List<ApexClass> classes = [
            SELECT Name, Body, ApiVersion, LengthWithoutComments
            FROM ApexClass
            WHERE NamespacePrefix = null AND LengthWithoutComments < 40000
            ORDER BY Name LIMIT 150];
        Integer linked = 0;
        for (ApexClass c : classes) {
            if (c.Body == null) {
                continue;
            }
            List<String> references = new List<String>();
            for (String apiName : known) {
                if (c.Body.contains(apiName)) {
                    references.add(apiName);
                }
            }
            c.Body = null;    // release heap before the next class
            if (references.isEmpty()) {
                continue;     // unreachable by traversal, so not worth a node
            }
            Boolean isTest = c.Name.endsWithIgnoreCase('Test')
                          || c.Name.startsWithIgnoreCase('Test');
            String id = 'apex:' + c.Name;
            doc.addNode(id, isTest ? 'TestClass' : 'ApexClass', c.Name, c.Name,
                '{"apiVersion":' + c.ApiVersion + ',"test":' + isTest + '}',
                c.LengthWithoutComments > 5000 ? 'High' : 'Medium',
                'METADATA ApexClass ' + c.Name, 'Salesforce');
            for (String apiName : references) {
                doc.addEdge(id, 'APEX_REFERENCES_SOBJECT', 'sobj:' + apiName,
                    'API name found in ApexClass.Body');
            }
            linked++;
        }
        doc.notes.add(linked + ' of ' + classes.size() + ' Apex classes reference '
            + 'a scoped object; the rest are omitted as unreachable');
    }

    // ----------------------------------------------------------------- helpers

    /**
     * Every object in the org, keyed by its flattened API name.
     *
     * Keys only. getGlobalDescribe() is cheap; calling getDescribe() on ~1,400
     * objects to read their labels is not, and would spend the CPU the export
     * needs. A label almost always flattens to the same string as its API name
     * ("Healthcare Provider" and HealthcareProvider both become
     * healthcareprovider), so this resolves references outside the pod without
     * a single describe call.
     */
    private static Map<String, String> orgIndex() {
        Map<String, String> byName = new Map<String, String>();
        for (String apiName : Schema.getGlobalDescribe().keySet()) {
            String flat = normalize(apiName);
            if (!byName.containsKey(flat)) {
                byName.put(flat, apiName);
            }
            if (apiName.endsWith('__c')) {
                String bare = normalize(apiName.removeEnd('__c'));
                if (!byName.containsKey(bare)) {
                    byName.put(bare, apiName);
                }
            }
        }
        return byName;
    }

    /**
     * Resolve an automation reference to an object, widening only on failure:
     * the pod scope first, then the whole org.
     *
     * The second step is what closes the Account gap. A reference that landed
     * outside the pod used to resolve to null and the entire flow was dropped,
     * so a Flow record-triggered on Account was absent from the graph at the
     * moment the console was asked whether that Flow existed. The honest
     * answer to "is Account out of scope" is to say so on the node, not to
     * pretend the automation is not there.
     */
    private static String resolveAnywhere(String reference, Set<String> known,
                                          Map<String, String> labelToApi,
                                          Map<String, String> orgByName) {
        String scoped = resolve(reference, known, labelToApi);
        if (scoped != null) {
            return scoped;
        }
        if (String.isBlank(reference)) {
            return null;
        }
        return orgByName.get(normalize(reference));
    }

    /**
     * A one-node stand-in for an object outside the pod that pod automation
     * fires on. No fields and no record types, so it costs a couple of hundred
     * bytes and cannot drag the object's whole column list into the graph.
     *
     * Returns false only when the boundary budget is spent, in which case the
     * caller drops the automation rather than emitting an edge to a node that
     * does not exist.
     */
    private static Boolean addBoundaryObject(AIGraphDocument doc, String apiName,
                                             Set<String> boundaryIds) {
        if (boundaryIds.contains(apiName)) {
            return true;
        }
        if (boundaryIds.size() >= MAX_BOUNDARY_OBJECTS) {
            return false;
        }
        boundaryIds.add(apiName);
        doc.addNode('sobj:' + apiName, 'SObject', apiName, apiName,
            '{"boundary":true}', 'Medium',
            'SCHEMA ' + apiName + ' · outside the pod scope, included because '
            + 'automation in scope fires on it', 'Salesforce');
        return true;
    }

    private static String resolve(String reference, Set<String> known,
                                  Map<String, String> labelToApi) {
        if (String.isBlank(reference)) {
            return null;
        }
        if (known.contains(reference)) {
            return reference;
        }
        String resolved = labelToApi.get(normalize(reference));
        return (resolved != null && known.contains(resolved)) ? resolved : null;
    }

    private static String normalize(String value) {
        return value == null ? '' : value.toLowerCase().replaceAll('[^a-z0-9]', '');
    }
}
