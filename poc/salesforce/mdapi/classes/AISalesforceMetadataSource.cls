/**
 * Live Salesforce metadata search. No callout, no configuration, no fixtures.
 *
 * Everything here reads the running org: Schema describe for objects, fields
 * and relationships, and SOQL over ApexClass, ApexTrigger and
 * FlowDefinitionView for automation. That is real data the moment it is
 * deployed, which is what makes the console demonstrable before the Semantica
 * service exists.
 *
 * What this is NOT: a graph. Intent resolution here is keyword matching
 * against live metadata, not traversal over precomputed typed edges. It finds
 * what a change touches directly and one hop out. Multi-hop blast radius,
 * reuse detection across capabilities and cross-source provenance are what the
 * graph layer adds, and they are why the graph layer exists.
 */
public with sharing class AISalesforceMetadataSource {

    private static final Integer MAX_OBJECTS = 5;
    private static final Integer MAX_FIELDS_PER_OBJECT = 8;
    private static final Integer MAX_AUTOMATION = 12;

    private static final Set<String> STOPWORDS = new Set<String>{
        'THE','AND','FOR','NOT','ADD','NEW','ALL','ANY','BUT','CAN','DOES','FROM',
        'HAS','HAVE','INTO','LOGIC','MAKE','MUST','NEED','ONLY','SHOULD','SURE',
        'THAT','THIS','WHEN','WILL','WITH','WOULD','WAS','ARE','CHANGE','CREATE',
        'UPDATE','MODIFY','FIELD','FIELDS','RECORD','RECORDS','PLEASE','WANT'
    };

    public class Result {
        public List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>();
        public Set<String> objectsMatched = new Set<String>();
        public String note;
    }

    /** Pull candidate identifiers out of free text. */
    public static Set<String> extractTerms(String text) {
        Set<String> terms = new Set<String>();
        if (String.isBlank(text)) {
            return terms;
        }
        for (String raw : text.toUpperCase().split('[^A-Z0-9_]+')) {
            if (raw.length() >= 3 && !STOPWORDS.contains(raw)) {
                terms.add(raw);
            }
        }
        return terms;
    }

    public static Result search(Set<String> terms) {
        Result r = new Result();
        if (terms.isEmpty()) {
            r.note = 'No searchable terms in the request.';
            return r;
        }

        // Match on API name without describing everything: describe is the
        // expensive call, so only matched types are described.
        Map<String, Schema.SObjectType> global = Schema.getGlobalDescribe();
        List<String> matched = new List<String>();
        for (String apiName : global.keySet()) {
            String upper = apiName.toUpperCase();
            for (String t : terms) {
                if (upper.contains(t)) {
                    matched.add(apiName);
                    break;
                }
            }
            if (matched.size() >= MAX_OBJECTS) {
                break;
            }
        }

        for (String apiName : matched) {
            describeObject(r, global.get(apiName), apiName, terms);
        }
        r.objectsMatched = new Set<String>(matched);

        addTriggers(r, terms);
        addFlows(r, terms);
        addApexClasses(r, terms);

        if (r.findings.isEmpty()) {
            r.note = 'Nothing in this org matched: ' + String.join(new List<String>(terms), ', ');
        }
        return r;
    }

    private static void describeObject(Result r, Schema.SObjectType sot,
                                       String apiName, Set<String> terms) {
        Schema.DescribeSObjectResult d = sot.getDescribe();
        Map<String, Schema.SObjectField> fields = d.fields.getMap();
        Integer fieldCount = fields.size();
        Integer rtCount = d.getRecordTypeInfos().size();

        r.findings.add(AIContextSlice.build(
            'sobj:' + apiName, 'SObject', d.getLabel(),
            'Matched the request text directly',
            'Direct', fieldCount > 100 ? 'High' : 'Medium', 'Salesforce',
            'SALESFORCE_SCHEMA describe(' + apiName + ') · ' + fieldCount
                + ' fields · ' + rtCount + ' record types · '
                + (d.isCustom() ? 'custom' : 'standard')));

        Integer added = 0;
        for (String fieldName : fields.keySet()) {
            if (added >= MAX_FIELDS_PER_OBJECT) {
                break;
            }
            String upper = fieldName.toUpperCase();
            Boolean hit = false;
            for (String t : terms) {
                if (upper.contains(t)) {
                    hit = true;
                    break;
                }
            }
            if (!hit) {
                continue;
            }
            Schema.DescribeFieldResult fd = fields.get(fieldName).getDescribe();
            String detail = String.valueOf(fd.getType());
            if (fd.getType() == Schema.DisplayType.REFERENCE
                    && !fd.getReferenceTo().isEmpty()) {
                detail += ' -> ' + fd.getReferenceTo()[0].getDescribe().getName();
            }
            r.findings.add(AIContextSlice.build(
                'field:' + apiName + '.' + fieldName, 'Field', fd.getLabel(),
                'SOBJECT_HAS_FIELD -> sobj:' + apiName,
                'Direct', fd.isCalculated() ? 'High' : 'Low', 'Salesforce',
                'SALESFORCE_SCHEMA ' + apiName + '.' + fieldName + ' · ' + detail
                    + (fd.isCalculated() ? ' · formula' : '')));
            added++;
        }
    }

    private static void addTriggers(Result r, Set<String> terms) {
        for (ApexTrigger t : [
                SELECT Name, TableEnumOrId, Status
                FROM ApexTrigger
                WHERE NamespacePrefix = null
                LIMIT 200]) {
            if (!matches(t.TableEnumOrId, terms) && !matches(t.Name, terms)) {
                continue;
            }
            r.findings.add(AIContextSlice.build(
                'trigger:' + t.Name, 'ApexTrigger', t.Name,
                'TRIGGER_FIRES_ON_SOBJECT -> sobj:' + t.TableEnumOrId,
                'One Hop', 'High', 'Salesforce',
                'SALESFORCE_METADATA ApexTrigger ' + t.Name + ' · on '
                    + t.TableEnumOrId + ' · ' + t.Status));
            if (r.findings.size() > MAX_AUTOMATION * 3) {
                return;
            }
        }
    }

    private static void addFlows(Result r, Set<String> terms) {
        Integer n = 0;
        for (FlowDefinitionView f : [
                SELECT ApiName, Label, ProcessType, TriggerType,
                       TriggerObjectOrEventLabel, VersionNumber
                FROM FlowDefinitionView
                WHERE IsActive = true
                LIMIT 300]) {
            if (n >= MAX_AUTOMATION) {
                break;
            }
            if (!matches(f.ApiName, terms) && !matches(f.TriggerObjectOrEventLabel, terms)) {
                continue;
            }
            String target = String.isBlank(f.TriggerObjectOrEventLabel)
                          ? '(not record-triggered)' : f.TriggerObjectOrEventLabel;
            r.findings.add(AIContextSlice.build(
                'flow:' + f.ApiName, 'Flow', f.Label,
                'FLOW_UPDATES_SOBJECT -> ' + target,
                'One Hop', 'High', 'Salesforce',
                'SALESFORCE_METADATA Flow ' + f.ApiName + ' v' + f.VersionNumber
                    + ' · ' + f.ProcessType
                    + (String.isBlank(f.TriggerType) ? '' : ' · ' + f.TriggerType)));
            n++;
        }
    }

    private static void addApexClasses(Result r, Set<String> terms) {
        Integer n = 0;
        for (ApexClass c : [
                SELECT Name, ApiVersion, LengthWithoutComments
                FROM ApexClass
                WHERE NamespacePrefix = null
                ORDER BY Name
                LIMIT 500]) {
            if (n >= MAX_AUTOMATION) {
                break;
            }
            if (!matches(c.Name, terms)) {
                continue;
            }
            r.findings.add(AIContextSlice.build(
                'apex:' + c.Name, 'ApexClass', c.Name,
                'Name matched the request text',
                'One Hop', c.LengthWithoutComments > 5000 ? 'High' : 'Medium',
                'Salesforce',
                'SALESFORCE_METADATA ApexClass ' + c.Name + ' · API '
                    + c.ApiVersion + ' · ' + c.LengthWithoutComments + ' chars'));
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
