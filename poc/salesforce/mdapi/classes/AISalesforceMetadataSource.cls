/**
 * Live search over the Network Services footprint in the running org.
 *
 * No callout and no configuration. Schema describe supplies objects, fields,
 * formulas, lookups and record types; SOQL over ApexClass, ApexTrigger and
 * FlowDefinitionView supplies automation. Scope comes from the pod's profile,
 * so the search covers what that team actually owns.
 *
 * Not a graph. This resolves what a change touches directly and one hop out by
 * matching names against live metadata. Multi-hop blast radius, reuse across
 * capabilities and cross-source edges need precomputed typed relationships,
 * which is the graph layer's job.
 *
 * Lightning components and validation rules are absent because neither is
 * reachable from Apex without the Tooling API. The search says so rather than
 * quietly omitting them.
 */
public with sharing class AISalesforceMetadataSource {

    private static final Integer MAX_OBJECTS = 4;
    private static final Integer MAX_FIELDS = 12;
    private static final Integer MAX_AUTOMATION = 10;

    private static final Set<String> STOPWORDS = new Set<String>{
        'THE','AND','FOR','NOT','ADD','NEW','ALL','ANY','BUT','CAN','DOES','FROM',
        'HAS','HAVE','INTO','LOGIC','MAKE','MUST','NEED','ONLY','SHOULD','SURE',
        'THAT','THIS','WHEN','WILL','WITH','WOULD','WAS','ARE','CHANGE','CREATE',
        'UPDATE','MODIFY','DELETE','REMOVE','RECORD','RECORDS','PLEASE','WANT',
        'CALLED','NAMED','FIELD','FIELDS','OBJECT','OBJECTS','ALREADY','EXIST',
        'EXISTS','PLUS','ALSO','SOME','EACH','BEEN','WHICH','THERE','THEIR'
    };

    public class Result {
        public List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>();
        public String resolvedObject;
        public Integer objectsSearched = 0;
        public List<String> notes = new List<String>();
    }

    public static Set<String> extractTerms(String text) {
        Set<String> terms = new Set<String>();
        if (String.isBlank(text)) {
            return terms;
        }
        for (String raw : text.toUpperCase().split('[^A-Z0-9_]+')) {
            if (raw.length() >= 3 && !STOPWORDS.contains(raw)) {
                terms.add(raw.endsWith('__C') ? raw.removeEnd('__C') : raw);
            }
        }
        return terms;
    }

    public static Result search(AIRequestIntent intent, AINetworkServicesScope scope) {
        Result r = new Result();
        Set<String> terms = new Set<String>(intent.terms);
        if (String.isNotBlank(intent.targetName)) {
            terms.addAll(extractTerms(intent.targetName));
        }
        if (terms.isEmpty()) {
            r.notes.add('No searchable terms in the request');
            return r;
        }

        Map<String, Schema.SObjectType> describeMap = Schema.getGlobalDescribe();
        List<String> targets = resolveObjects(describeMap, intent, scope, terms);
        r.objectsSearched = targets.size();
        if (!targets.isEmpty()) {
            r.resolvedObject = targets[0];
        }

        for (String apiName : targets) {
            describeObject(r, describeMap.get(apiName), apiName, terms);
        }
        addTriggers(r, terms, new Set<String>(targets));
        addFlows(r, terms, scope);
        addApexClasses(r, terms);

        if (!scope.profileFound) {
            r.notes.add(scope.note);
        }
        r.notes.add('Lightning components and validation rules need the Tooling API, '
                  + 'which is not configured');
        return r;
    }

    // --------------------------------------------------------------- objects

    private static List<String> resolveObjects(Map<String, Schema.SObjectType> describeMap,
            AIRequestIntent intent, AINetworkServicesScope scope, Set<String> terms) {
        List<String> targets = new List<String>();

        // An explicitly named object wins over keyword matching.
        if (String.isNotBlank(intent.targetObject)) {
            String wanted = intent.targetObject.toLowerCase().replaceAll('[^a-z0-9]', '');
            for (String apiName : describeMap.keySet()) {
                String bare = apiName.toLowerCase().removeEnd('__c').replaceAll('[^a-z0-9]', '');
                if (bare == wanted && scope.covers(apiName)) {
                    targets.add(apiName);
                    return targets;
                }
            }
        }

        for (String apiName : describeMap.keySet()) {
            if (targets.size() >= MAX_OBJECTS) {
                break;
            }
            if (!scope.covers(apiName)) {
                continue;
            }
            String upper = apiName.toUpperCase();
            for (String t : terms) {
                if (upper.contains(t)) {
                    targets.add(apiName);
                    break;
                }
            }
        }
        return targets;
    }

    private static void describeObject(Result r, Schema.SObjectType sot,
                                       String apiName, Set<String> terms) {
        if (sot == null) {
            return;
        }
        Schema.DescribeSObjectResult d = sot.getDescribe();
        Map<String, Schema.SObjectField> fields = d.fields.getMap();
        List<Schema.RecordTypeInfo> rts = d.getRecordTypeInfos();

        r.findings.add(AIContextSlice.build(
            'sobj:' + apiName, 'SObject', d.getLabel(),
            'The object this request targets',
            'Direct', fields.size() > 100 ? 'High' : 'Medium', 'Salesforce',
            'SCHEMA describe(' + apiName + ') · ' + fields.size() + ' fields · '
                + (rts.size() - 1) + ' record types · '
                + (d.isCustom() ? 'custom' : 'standard')));

        for (Schema.RecordTypeInfo rt : rts) {
            if (rt.isMaster() || !rt.isAvailable()) {
                continue;
            }
            r.findings.add(AIContextSlice.build(
                'rt:' + apiName + '.' + rt.getDeveloperName(), 'RecordType',
                rt.getName(),
                'SOBJECT_HAS_RECORDTYPE -> sobj:' + apiName,
                'Direct', 'Low', 'Salesforce',
                'SCHEMA record type ' + rt.getDeveloperName() + ' on ' + apiName
                    + (rt.isDefaultRecordTypeMapping() ? ' · default' : '')));
        }

        Integer added = 0;
        for (String fieldName : fields.keySet()) {
            if (added >= MAX_FIELDS) {
                r.notes.add('Field list truncated at ' + MAX_FIELDS + ' for ' + apiName);
                break;
            }
            if (!matches(fieldName, terms)) {
                continue;
            }
            Schema.DescribeFieldResult fd = fields.get(fieldName).getDescribe();
            String detail = String.valueOf(fd.getType());
            if (fd.getType() == Schema.DisplayType.REFERENCE && !fd.getReferenceTo().isEmpty()) {
                detail += ' -> ' + fd.getReferenceTo()[0].getDescribe().getName();
            }
            if (fd.getLength() > 0) {
                detail += '(' + fd.getLength() + ')';
            }
            r.findings.add(AIContextSlice.build(
                'field:' + apiName + '.' + fd.getName(), 'Field', fd.getLabel(),
                'SOBJECT_HAS_FIELD -> sobj:' + apiName,
                'Direct', fd.isCalculated() ? 'High' : 'Low', 'Salesforce',
                'SCHEMA ' + apiName + '.' + fd.getName() + ' · ' + detail
                    + (fd.isCalculated() ? ' · formula' : '')
                    + (fd.isCustom() ? ' · custom' : ' · standard')));
            added++;
        }
    }

    // ------------------------------------------------------------ automation

    private static void addTriggers(Result r, Set<String> terms, Set<String> objects) {
        List<ApexTrigger> triggers = [
            SELECT Name, TableEnumOrId, Status
            FROM ApexTrigger WHERE NamespacePrefix = null LIMIT 200];
        for (ApexTrigger t : triggers) {
            if (!objects.contains(t.TableEnumOrId) && !matches(t.Name, terms)) {
                continue;
            }
            r.findings.add(AIContextSlice.build(
                'trigger:' + t.Name, 'ApexTrigger', t.Name,
                'TRIGGER_FIRES_ON_SOBJECT -> sobj:' + t.TableEnumOrId,
                'One Hop', 'High', 'Salesforce',
                'METADATA ApexTrigger ' + t.Name + ' · on ' + t.TableEnumOrId
                    + ' · ' + t.Status));
        }
    }

    private static void addFlows(Result r, Set<String> terms, AINetworkServicesScope scope) {
        Integer n = 0;
        // FlowDefinitionView does not support queryMore(), so this must be a
        // list assignment capped at one batch, never a SOQL for-loop.
        List<FlowDefinitionView> flows = [
            SELECT ApiName, Label, ProcessType, TriggerType,
                   TriggerObjectOrEventLabel, VersionNumber
            FROM FlowDefinitionView WHERE IsActive = true LIMIT 200];
        for (FlowDefinitionView f : flows) {
            if (n >= MAX_AUTOMATION) {
                r.notes.add('Flow list truncated at ' + MAX_AUTOMATION);
                break;
            }
            if (!matches(f.ApiName, terms) && !matches(f.TriggerObjectOrEventLabel, terms)) {
                continue;
            }
            String target = String.isBlank(f.TriggerObjectOrEventLabel)
                          ? 'not record-triggered' : f.TriggerObjectOrEventLabel;
            r.findings.add(AIContextSlice.build(
                'flow:' + f.ApiName, 'Flow', f.Label,
                'FLOW_UPDATES_SOBJECT -> ' + target,
                'One Hop', 'High', 'Salesforce',
                'METADATA Flow ' + f.ApiName + ' v' + f.VersionNumber + ' · '
                    + f.ProcessType
                    + (String.isBlank(f.TriggerType) ? '' : ' · ' + f.TriggerType)));
            n++;
        }
    }

    private static void addApexClasses(Result r, Set<String> terms) {
        Integer n = 0;
        List<ApexClass> classes = [
            SELECT Name, ApiVersion, LengthWithoutComments
            FROM ApexClass WHERE NamespacePrefix = null ORDER BY Name LIMIT 500];
        for (ApexClass c : classes) {
            if (n >= MAX_AUTOMATION) {
                r.notes.add('Apex class list truncated at ' + MAX_AUTOMATION);
                break;
            }
            if (!matches(c.Name, terms)) {
                continue;
            }
            r.findings.add(AIContextSlice.build(
                'apex:' + c.Name, 'ApexClass', c.Name,
                'Class name matched the request',
                'One Hop', c.LengthWithoutComments > 5000 ? 'High' : 'Medium',
                'Salesforce',
                'METADATA ApexClass ' + c.Name + ' · API ' + c.ApiVersion + ' · '
                    + c.LengthWithoutComments + ' chars'));
            n++;
        }
    }

    private static Boolean matches(String value, Set<String> terms) {
        if (String.isBlank(value)) {
            return false;
        }
        String upper = value.toUpperCase();
        for (String t : terms) {
            if (upper.contains(t)) {
                return true;
            }
        }
        return false;
    }
}
