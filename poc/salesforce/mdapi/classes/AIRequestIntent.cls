/**
 * Works out what the request is actually asking for.
 *
 * Rule-based, not a model. It reads an action, a component type, a target name
 * and a target object out of free text. It will misread some phrasings, which
 * is exactly why the console shows its reading back to the user before doing
 * anything: a wrong interpretation is visible and correctable, not silent.
 */
public with sharing class AIRequestIntent {

    public String action = 'Analyze';        // Create | Update | Delete | Analyze
    public String targetType = 'Unknown';    // Field | SObject | Flow | ...
    public String targetName;
    public String targetObject;
    public String targetDataType;

    /**
     * Component requests name a thing to build: "create a field called X".
     * Behaviour requests describe what should happen: "when an Account is
     * created, also create a HealthcareProvider".
     *
     * They need completely different analysis. Treating the second as the
     * first is how "when Account gets created I want to create
     * HealthcareProvider" came back Safe to Create while a Flow already did
     * exactly that.
     */
    public String requestShape = 'Component';   // Component | Behaviour
    public String triggerObject;                // Account
    public String triggerEvent;                 // Created | Updated | Deleted
    public List<String> affectedObjects = new List<String>();
    public Set<String> terms = new Set<String>();
    public String summary;

    private static final Map<String, String> ACTIONS = new Map<String, String>{
        'CREATE' => 'Create', 'ADD' => 'Create', 'NEW' => 'Create',
        'INTRODUCE' => 'Create', 'BUILD' => 'Create',
        'UPDATE' => 'Update', 'CHANGE' => 'Update', 'MODIFY' => 'Update',
        'FIX' => 'Update', 'AMEND' => 'Update', 'ADJUST' => 'Update',
        'DELETE' => 'Delete', 'REMOVE' => 'Delete', 'RETIRE' => 'Delete'
    };

    // Longest phrases first, so "validation rule" wins over "rule".
    private static final List<String> TYPE_PHRASES = new List<String>{
        'VALIDATION RULE', 'RECORD TYPE', 'LIGHTNING COMPONENT', 'APEX CLASS',
        'PERMISSION SET', 'CUSTOM FIELD', 'CUSTOM OBJECT',
        'TRIGGER', 'FLOW', 'FIELD', 'OBJECT', 'CLASS', 'LWC', 'COMPONENT'
    };
    private static final Map<String, String> TYPE_OF = new Map<String, String>{
        'VALIDATION RULE' => 'ValidationRule', 'RECORD TYPE' => 'RecordType',
        'LIGHTNING COMPONENT' => 'LightningComponent', 'APEX CLASS' => 'ApexClass',
        'PERMISSION SET' => 'PermissionSet', 'CUSTOM FIELD' => 'Field',
        'CUSTOM OBJECT' => 'SObject', 'TRIGGER' => 'ApexTrigger',
        'FLOW' => 'Flow', 'FIELD' => 'Field', 'OBJECT' => 'SObject',
        'CLASS' => 'ApexClass', 'LWC' => 'LightningComponent',
        'COMPONENT' => 'LightningComponent'
    };

    public static AIRequestIntent parse(String text) {
        AIRequestIntent i = new AIRequestIntent();
        if (String.isBlank(text)) {
            i.summary = 'Empty request.';
            return i;
        }
        String upper = text.toUpperCase();
        i.terms = AISalesforceMetadataSource.extractTerms(text);

        for (String word : upper.split('[^A-Z0-9_]+')) {
            if (ACTIONS.containsKey(word)) {
                i.action = ACTIONS.get(word);
                break;
            }
        }

        for (String phrase : TYPE_PHRASES) {
            if (upper.contains(phrase)) {
                i.targetType = TYPE_OF.get(phrase);
                break;
            }
        }

        i.targetName = extractName(text);
        i.targetObject = extractObject(text);
        i.targetDataType = extractDataType(text);
        detectBehaviour(i, text);
        i.summary = describe(i);
        return i;
    }

    private static final Map<String, String> DATA_TYPES = new Map<String, String>{
        'DATETIME' => 'DateTime', 'DATE' => 'Date', 'TEXTAREA' => 'TextArea',
        'TEXT' => 'Text', 'NUMBER' => 'Number', 'CURRENCY' => 'Currency',
        'CHECKBOX' => 'Checkbox', 'PICKLIST' => 'Picklist', 'EMAIL' => 'Email',
        'PHONE' => 'Phone', 'URL' => 'URL', 'FORMULA' => 'Formula',
        'LOOKUP' => 'Lookup', 'PERCENT' => 'Percent'
    };

    // Apex Map key order is not guaranteed, so the fallback scan needs an
    // explicit order: DATETIME must be tried before DATE, TEXTAREA before TEXT.
    private static final List<String> TYPE_SCAN_ORDER = new List<String>{
        'DATETIME', 'DATE', 'TEXTAREA', 'TEXT', 'CURRENCY', 'NUMBER',
        'CHECKBOX', 'PICKLIST', 'EMAIL', 'PHONE', 'URL', 'FORMULA',
        'LOOKUP', 'PERCENT'
    };

    /** Words that describe a request rather than name anything in it. */
    private static final Set<String> NEVER_A_NAME = new Set<String>{
        'type', 'data', 'datatype', 'field', 'fields', 'object', 'objects',
        'new', 'custom', 'standard', 'a', 'an', 'the', 'this', 'that',
        'value', 'values', 'flow', 'class', 'trigger', 'component', 'rule',
        'record', 'records', 'date', 'text', 'number', 'checkbox', 'picklist',
        'formula', 'lookup', 'currency', 'email', 'phone', 'url', 'percent'
    };

    private static final Pattern OBJECT_CLAUSE = Pattern.compile(
        '(?i)\\s*\\b(?:in|on|to|for)\\s+(?:the\\s+)?' +
        '([A-Za-z0-9_]{3,60})(?:\\s+object)?\\s*$');

    /**
     * Pull the component name out of free text.
     *
     * Ordered by how explicit the phrasing is. The comma rule matters most in
     * practice, because people write "effective from date, date data type
     * field on X" and the name is everything before the first comma.
     */
    private static String extractName(String text) {
        Matcher m = Pattern.compile('["\']([^"\']{2,60})["\']').matcher(text);
        if (m.find()) {
            return clean(m.group(1));
        }

        m = Pattern.compile(
            '(?i)(?:called|named)\\s+["\']?([A-Za-z0-9_ ]{2,60}?)["\']?' +
            '(?:\\s+(?:on|in|to|for|of|so|which|that|with)\\b|[.,]|$)').matcher(text);
        if (m.find()) {
            return clean(m.group(1));
        }

        String body = stripObjectClause(text);

        if (body.contains(',')) {
            String candidate =
                stripTypeNouns(clean(stripLeadIn(body.substringBefore(','))));
            if (isUsableName(candidate)) {
                return candidate;
            }
        }

        // Short, direct phrasing: "create effective from date field" leaves
        // "effective from date" once the verb and the component noun are gone.
        // This has to be tried before the word-before-a-type-noun rule below,
        // which would take only "date" and miss the field that already exists.
        String residue = stripTypeNouns(clean(stripLeadIn(body)));
        if (isUsableName(residue) && wordCount(residue) <= 5) {
            return residue;
        }

        m = Pattern.compile(
            '(?i)\\b([A-Za-z0-9_]{2,40})\\s+' +
            '(?:field|object|flow|trigger|class|component)\\b').matcher(body);
        if (m.find()) {
            String candidate = clean(m.group(1));
            if (isUsableName(candidate)) {
                return candidate;
            }
        }

        return isUsableName(residue) ? residue : null;
    }

    private static Integer wordCount(String value) {
        return String.isBlank(value) ? 0 : value.trim().split('\\s+').size();
    }

    /**
     * Drop a trailing or leading component noun from a name.
     *
     * "create effective from date field in healthcarefacility object" left the
     * name as "effective from date field". That normalises to
     * effectivefromdatefield, which does not equal effectivefromdate, so the
     * duplicate check missed a field the near-match logic was listing on the
     * same screen.
     */
    private static String stripTypeNouns(String value) {
        if (String.isBlank(value)) {
            return value;
        }
        String out = value.trim();
        Pattern trailing = Pattern.compile(
            '(?i)\\s+(field|fields|object|objects|flow|trigger|class|component|'
            + 'record|records|rule|type)$');
        Pattern leading = Pattern.compile(
            '(?i)^(field|object|flow|trigger|class|component|record|rule|type)\\s+');
        for (Integer i = 0; i < 3; i++) {
            Matcher t = trailing.matcher(out);
            if (t.find()) {
                out = out.substring(0, t.start()).trim();
                continue;
            }
            Matcher l = leading.matcher(out);
            if (l.find()) {
                out = out.substring(l.end()).trim();
                continue;
            }
            break;
        }
        return out;
    }

    private static String extractObject(String text) {
        Matcher m = OBJECT_CLAUSE.matcher(text.trim());
        if (m.find()) {
            String candidate = m.group(1);
            if (!NEVER_A_NAME.contains(candidate.toLowerCase())) {
                return candidate;
            }
        }
        // Fall back to any "in|on|to|for X" earlier in the sentence.
        m = Pattern.compile(
            '(?i)\\b(?:in|on|to|for)\\s+(?:the\\s+)?' +
            '([A-Za-z0-9_]{3,60})(?:\\s+object)?\\b').matcher(text);
        while (m.find()) {
            String candidate = m.group(1);
            if (!NEVER_A_NAME.contains(candidate.toLowerCase())
                    && !ACTIONS.containsKey(candidate.toUpperCase())) {
                return candidate;
            }
        }
        return null;
    }

    /** "date data type" wins over a bare type word appearing in a name. */
    private static String extractDataType(String text) {
        Matcher m = Pattern.compile(
            '(?i)\\b([A-Za-z]+)\\s+data\\s*type\\b').matcher(text);
        if (m.find() && DATA_TYPES.containsKey(m.group(1).toUpperCase())) {
            return DATA_TYPES.get(m.group(1).toUpperCase());
        }
        String upper = text.toUpperCase();
        for (String key : TYPE_SCAN_ORDER) {
            if (Pattern.compile('\\b' + key + '\\b').matcher(upper).find()) {
                return DATA_TYPES.get(key);
            }
        }
        return null;
    }

    private static String stripObjectClause(String text) {
        Matcher m = OBJECT_CLAUSE.matcher(text.trim());
        return m.find() ? text.trim().substring(0, m.start()) : text.trim();
    }

    /** Drop a leading verb and article so "create a X" yields "X". */
    private static String stripLeadIn(String text) {
        String out = text.trim();
        for (Integer i = 0; i < 3; i++) {
            Matcher m = Pattern.compile(
                '(?i)^(create|add|new|build|introduce|update|change|modify|fix|' +
                'delete|remove|retire|please|a|an|the)\\b\\s*').matcher(out);
            if (!m.find()) {
                break;
            }
            out = out.substring(m.end());
        }
        return out;
    }

    private static String clean(String value) {
        return value == null ? null
            : value.trim().replaceAll('[\\s]+', ' ').replaceAll('^[,.;:]+|[,.;:]+$', '').trim();
    }

    private static Boolean isUsableName(String candidate) {
        if (String.isBlank(candidate) || candidate.length() < 2 || candidate.length() > 60) {
            return false;
        }
        if (NEVER_A_NAME.contains(candidate.toLowerCase())) {
            return false;
        }
        // "date data type" is a description, not a name.
        String collapsed = candidate.toLowerCase().replaceAll('[^a-z ]', '');
        for (String word : collapsed.split(' ')) {
            if (!NEVER_A_NAME.contains(word)) {
                return true;
            }
        }
        return false;
    }

    private static final Map<String, String> EVENTS = new Map<String, String>{
        'CREATED' => 'Created', 'CREATE' => 'Created', 'INSERTED' => 'Created',
        'UPDATED' => 'Updated', 'UPDATE' => 'Updated', 'EDITED' => 'Updated',
        'DELETED' => 'Deleted', 'DELETE' => 'Deleted'
    };

    /**
     * "when X is created ... create Y and Z" is a behaviour, not a component.
     * The give-away is a trigger clause: when / whenever / if / on ... plus a
     * lifecycle verb.
     */
    private static void detectBehaviour(AIRequestIntent i, String text) {
        Matcher m = Pattern.compile(
            '(?i)\\b(?:when|whenever|if|on)\\s+(?:an?\\s+|the\\s+)?' +
            '([A-Za-z0-9_]{3,60})\\s+(?:record\\s+)?' +
            '(?:is|gets|are|get|was|has\\s+been)?\\s*' +
            '(created|create|inserted|updated|update|edited|deleted|delete)\\b'
        ).matcher(text);
        if (!m.find()) {
            return;
        }
        i.requestShape = 'Behaviour';
        i.triggerObject = m.group(1);
        i.triggerEvent = EVENTS.get(m.group(2).toUpperCase());

        // Objects named after the trigger clause are what the behaviour writes.
        String tail = text.substring(m.end());
        Matcher objects = Pattern.compile(
            '(?i)\\b([A-Z][A-Za-z0-9_]{3,60}(?:__c)?)\\b').matcher(tail);
        Set<String> seen = new Set<String>();
        while (objects.find()) {
            String candidate = objects.group(1);
            String key = candidate.toLowerCase();
            if (NEVER_A_NAME.contains(key) || ACTIONS.containsKey(candidate.toUpperCase())
                    || key == i.triggerObject.toLowerCase() || !seen.add(key)) {
                continue;
            }
            i.affectedObjects.add(candidate);
        }
        // A behaviour has no single component name to duplicate-check.
        i.targetName = null;
        i.targetObject = i.triggerObject;
        i.targetType = 'Unknown';
    }

    private static String describe(AIRequestIntent i) {
        if (i.requestShape == 'Behaviour') {
            String line = 'When a ' + i.triggerObject + ' is '
                + (i.triggerEvent == null ? 'changed' : i.triggerEvent.toLowerCase());
            if (!i.affectedObjects.isEmpty()) {
                line += ', act on ' + String.join(i.affectedObjects, ' and ');
            }
            return line;
        }
        return describeComponent(i);
    }

    private static String describeComponent(AIRequestIntent i) {
        List<String> parts = new List<String>{ i.action };
        parts.add(i.targetType == 'Unknown' ? 'component' : 'a ' + label(i.targetType));
        if (String.isNotBlank(i.targetName)) {
            parts.add('named "' + i.targetName + '"');
        }
        if (String.isNotBlank(i.targetDataType)) {
            parts.add('(' + i.targetDataType + ')');
        }
        if (String.isNotBlank(i.targetObject)) {
            parts.add('on ' + i.targetObject);
        }
        return String.join(parts, ' ');
    }

    private static String label(String t) {
        Map<String, String> friendly = new Map<String, String>{
            'SObject' => 'object', 'Field' => 'field', 'Flow' => 'flow',
            'ApexClass' => 'Apex class', 'ApexTrigger' => 'trigger',
            'LightningComponent' => 'Lightning component',
            'ValidationRule' => 'validation rule', 'RecordType' => 'record type',
            'PermissionSet' => 'permission set'
        };
        return friendly.containsKey(t) ? friendly.get(t) : t;
    }
}
