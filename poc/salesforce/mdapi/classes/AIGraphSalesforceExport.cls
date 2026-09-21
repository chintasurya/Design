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

    /** Apex read limits. Bodies are fetched in chunks so heap stays bounded. */
    private static final Integer MAX_CLASSES = 400;
    private static final Integer BODY_CHUNK = 25;

    /**
     * Where the Apex scan gives up, of the 60,000 ms an async transaction has.
     * Stopping early and saying so beats a LimitException that loses the whole
     * export, and beats finishing quietly with chains half walked.
     */
    private static final Integer CPU_BUDGET_MS = 40000;

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

        // The names, not just the count. A note reading "36 objects in scope"
        // cannot be checked by anyone, and it is what made "is Account in
        // scope?" unanswerable without a Developer Console. At roughly 20
        // bytes an object this is free against a megabyte of JSON.
        doc.notes.add(targets.size() + ' objects in scope: ' + nameList(targets));
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

        Map<String, Set<String>> triggerCalls =
            addTriggers(doc, known, labelToApi, orgByName, boundaryIds);
        addFlows(doc, known, labelToApi, orgByName, boundaryIds);
        addApexClasses(doc, known, triggerCalls);

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

    /** A readable list, truncated rather than allowed to grow unbounded. */
    private static String nameList(List<String> names) {
        Integer cap = 120;
        if (names.size() <= cap) {
            return String.join(names, ', ');
        }
        List<String> head = new List<String>();
        for (Integer n = 0; n < cap; n++) {
            head.add(names[n]);
        }
        return String.join(head, ', ') + ', and ' + (names.size() - cap) + ' more';
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
        for (String fieldName : fieldOrder(fields, apiName)) {
            if (n++ >= MAX_FIELDS_PER_OBJECT) {
                doc.notes.add('Fields truncated at ' + MAX_FIELDS_PER_OBJECT
                    + ' for ' + apiName + ', custom fields kept first');
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

    /**
     * Which fields to take, and in what order, when there are too many.
     *
     * Account, Contact, Lead, Opportunity, Case and Task carry hundreds of
     * fields each and most belong to other pods. The pod's own data is in its
     * custom fields, so those go first and standard fields fill what is left.
     *
     * This is a proxy for what was actually wanted, which is the fields a
     * Network Services record type can see. Record type to field visibility
     * runs through page layout assignments, and describe() does not expose
     * those, so it needs the Metadata API. A proxy that admits to being one
     * is worth more than a filter claiming a precision it does not have.
     */
    private static List<String> fieldOrder(
            Map<String, Schema.SObjectField> fields, String apiName) {
        List<String> ordered = new List<String>(fields.keySet());
        if (!AINetworkServicesPod.TRIM_FIELDS_ON.contains(apiName.toLowerCase())
                || fields.size() <= MAX_FIELDS_PER_OBJECT) {
            return ordered;
        }
        List<String> custom = new List<String>();
        List<String> standard = new List<String>();
        for (String fieldName : ordered) {
            if (fields.get(fieldName).getDescribe().isCustom()) {
                custom.add(fieldName);
            } else {
                standard.add(fieldName);
            }
        }
        custom.addAll(standard);
        return custom;
    }

    /**
     * Triggers, and the classes they hand off to.
     *
     * A trigger body is almost always two lines that call a handler, so the
     * trigger alone answers nothing. The handler names are returned for the
     * Apex scan to turn into edges, which is what makes AHC_AccountTrigger the
     * start of a chain rather than a dead end.
     */
    private static Map<String, Set<String>> addTriggers(
            AIGraphDocument doc, Set<String> known,
            Map<String, String> labelToApi, Map<String, String> orgByName,
            Set<String> boundaryIds) {
        Map<String, Set<String>> handlerNames = new Map<String, Set<String>>();
        List<ApexTrigger> triggers = [
            SELECT Name, Body, TableEnumOrId, Status, ApiVersion
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
            Boolean pod = AINetworkServicesPod.namedForPod(t.Name);
            String id = 'trigger:' + t.Name;
            doc.addNode(id, 'ApexTrigger', t.Name, t.Name,
                '{"status":"' + t.Status + '","pod":' + pod + '}', 'High',
                'METADATA ApexTrigger on ' + onObject
                    + (pod ? ' · Network Services entry point' : ''),
                'Salesforce');
            doc.addEdge(id, 'TRIGGER_FIRES_ON_SOBJECT', 'sobj:' + onObject,
                'ApexTrigger.TableEnumOrId');

            if (t.Body != null) {
                // Every identifier in the body, lowercased. Which of them
                // are real classes is not knowable here; the Apex scan holds
                // that map and resolves them, which also fixes the casing.
                Set<String> called = new Set<String>();
                for (String token : t.Body.split('[^A-Za-z0-9_]+')) {
                    if (token.length() > 3) {
                        called.add(token.toLowerCase());
                    }
                }
                handlerNames.put(t.Name, called);
            }
        }
        return handlerNames;
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
            Boolean pod = AINetworkServicesPod.namedForPod(f.ApiName)
                       || AINetworkServicesPod.namedForPod(f.Label);
            String id = 'flow:' + f.ApiName;
            doc.addNode(id, 'Flow', f.Label, f.ApiName,
                '{"processType":"' + f.ProcessType + '","version":'
                    + f.VersionNumber + ',"pod":' + pod + '}', 'High',
                'METADATA Flow ' + f.ApiName + ' v' + f.VersionNumber
                    + (pod ? ' · Network Services automation' : ''),
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

    /**
     * Apex classes, what they touch, and what they call.
     *
     * Two changes from reading bodies for object names alone, both of which a
     * question like "how is an HFN generated" depends on:
     *
     * Whole identifiers, not substrings. body.contains('Account') is true of a
     * class that only mentions AccountingCode, which is the same fault that
     * made "UPDATE" match the term "DATE". The body is split into identifier
     * tokens once and matched against a map, which is both correct and cheaper
     * than one contains() per object per class.
     *
     * Call edges. A trigger handler is useless on its own: the logic lives in
     * the class it delegates to, and in the class that one delegates to. Those
     * chains are now edges, so a traversal that starts at an object reaches
     * the handler that writes it and then the classes behind that handler.
     */
    private static void addApexClasses(AIGraphDocument doc, Set<String> known,
                                       Map<String, Set<String>> triggerCalls) {
        // Headers first, bodies in chunks. Selecting several hundred bodies in
        // one query puts megabytes of source on the heap before a single one
        // has been read, and the heap is the binding constraint here.
        List<ApexClass> headers = [
            SELECT Id, Name, ApiVersion, LengthWithoutComments
            FROM ApexClass
            WHERE NamespacePrefix = null AND LengthWithoutComments < 40000
            ORDER BY Name LIMIT :MAX_CLASSES];

        Map<String, ApexClass> headerOf = new Map<String, ApexClass>();
        Map<String, String> classByLower = new Map<String, String>();
        List<Id> classIds = new List<Id>();
        for (ApexClass c : headers) {
            headerOf.put(c.Name, c);
            classByLower.put(c.Name.toLowerCase(), c.Name);
            classIds.add(c.Id);
        }
        Map<String, String> objectByLower = new Map<String, String>();
        for (String apiName : known) {
            objectByLower.put(apiName.toLowerCase(), apiName);
        }

        Map<String, Set<String>> objectRefs = new Map<String, Set<String>>();
        Map<String, Set<String>> callRefs = new Map<String, Set<String>>();
        Integer scanned = 0;
        Boolean ranOut = false;

        for (Integer offset = 0; offset < classIds.size(); offset += BODY_CHUNK) {
            if (Limits.getCpuTime() > CPU_BUDGET_MS
                    || Limits.getHeapSize() > Limits.getLimitHeapSize() / 2) {
                ranOut = true;
                break;
            }
            List<Id> chunk = new List<Id>();
            for (Integer n = offset;
                    n < classIds.size() && n < offset + BODY_CHUNK; n++) {
                chunk.add(classIds[n]);
            }
            for (ApexClass c : [SELECT Id, Name, Body FROM ApexClass
                                WHERE Id IN :chunk]) {
                if (c.Body == null) {
                    continue;
                }
                Set<String> objectsHit = new Set<String>();
                Set<String> callsHit = new Set<String>();
                String self = c.Name.toLowerCase();
                for (String token : c.Body.split('[^A-Za-z0-9_]+')) {
                    String key = token.toLowerCase();
                    if (objectByLower.containsKey(key)) {
                        objectsHit.add(objectByLower.get(key));
                    } else if (classByLower.containsKey(key) && key != self) {
                        callsHit.add(classByLower.get(key));
                    }
                }
                c.Body = null;       // release heap before the next class
                scanned++;
                if (!objectsHit.isEmpty()) {
                    objectRefs.put(c.Name, objectsHit);
                }
                if (!callsHit.isEmpty()) {
                    callRefs.put(c.Name, callsHit);
                }
            }
        }

        // A node still has to earn its place with an edge, so work out what is
        // touched before emitting anything. A class nothing calls and which
        // touches nothing is unreachable by traversal and therefore noise.
        Map<String, Set<String>> resolvedTriggerCalls =
            new Map<String, Set<String>>();
        for (String triggerName : triggerCalls.keySet()) {
            Set<String> real = new Set<String>();
            for (String candidate : triggerCalls.get(triggerName)) {
                if (classByLower.containsKey(candidate)) {
                    real.add(classByLower.get(candidate));
                }
            }
            if (!real.isEmpty()) {
                resolvedTriggerCalls.put(triggerName, real);
            }
        }

        Set<String> touched = new Set<String>();
        touched.addAll(objectRefs.keySet());
        touched.addAll(callRefs.keySet());
        for (Set<String> called : callRefs.values()) {
            touched.addAll(called);
        }
        for (Set<String> called : resolvedTriggerCalls.values()) {
            touched.addAll(called);
        }

        Integer emitted = 0;
        for (String name : touched) {
            ApexClass c = headerOf.get(name);
            if (c == null) {
                continue;
            }
            emitted++;
            Boolean isTest = name.endsWithIgnoreCase('Test')
                          || name.startsWithIgnoreCase('Test');
            Boolean pod = AINetworkServicesPod.namedForPod(name);
            doc.addNode('apex:' + name, isTest ? 'TestClass' : 'ApexClass',
                name, name,
                '{"apiVersion":' + c.ApiVersion + ',"test":' + isTest
                    + ',"pod":' + pod + '}',
                c.LengthWithoutComments > 5000 ? 'High' : 'Medium',
                'METADATA ApexClass ' + name
                    + (pod ? ' · named for the Network Services pod' : ''),
                'Salesforce');
        }

        Integer callEdges = 0;
        for (String name : objectRefs.keySet()) {
            if (!touched.contains(name) || headerOf.get(name) == null) {
                continue;
            }
            for (String apiName : objectRefs.get(name)) {
                doc.addEdge('apex:' + name, 'APEX_REFERENCES_SOBJECT',
                    'sobj:' + apiName, 'identifier in ApexClass.Body');
            }
        }
        for (String name : callRefs.keySet()) {
            if (headerOf.get(name) == null) {
                continue;
            }
            for (String called : callRefs.get(name)) {
                if (headerOf.get(called) == null) {
                    continue;
                }
                doc.addEdge('apex:' + name, 'APEX_CALLS_APEX',
                    'apex:' + called, 'class name in ApexClass.Body');
                callEdges++;
            }
        }
        for (String triggerName : resolvedTriggerCalls.keySet()) {
            for (String called : resolvedTriggerCalls.get(triggerName)) {
                doc.addEdge('trigger:' + triggerName, 'TRIGGER_CALLS_APEX',
                    'apex:' + called, 'class name in ApexTrigger.Body');
                callEdges++;
            }
        }

        doc.notes.add(emitted + ' Apex classes reachable from a scoped '
            + 'object or a call chain, out of ' + scanned + ' scanned of '
            + headers.size() + ' readable; ' + callEdges + ' call edges, which '
            + 'is what lets a handler\'s handler be found');
        if (ranOut) {
            doc.notes.add('The Apex scan stopped early on CPU or heap after '
                + scanned + ' classes. Call chains past that point are absent '
                + 'from this graph rather than known to be empty');
        }
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
