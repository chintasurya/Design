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
        i.summary = describe(i);
        return i;
    }

    /** "called X", "named X", a quoted string, or the word before the type. */
    private static String extractName(String text) {
        Matcher m = Pattern.compile(
            '(?i)(?:called|named)\\s+["\']?([A-Za-z0-9_ ]{2,40}?)["\']?' +
            '(?:\\s+(?:on|in|to|for|of|so|which|that)\\b|[.,]|$)').matcher(text);
        if (m.find()) {
            return m.group(1).trim();
        }
        m = Pattern.compile('["\']([^"\']{2,40})["\']').matcher(text);
        if (m.find()) {
            return m.group(1).trim();
        }
        m = Pattern.compile(
            '(?i)\\b([A-Za-z0-9_]{2,40})\\s+' +
            '(?:field|object|flow|trigger|class|component)\\b').matcher(text);
        if (m.find()) {
            String candidate = m.group(1);
            if (!(new Set<String>{'a','an','the','new','custom','this','that'}
                    .contains(candidate.toLowerCase()))) {
                return candidate;
            }
        }
        return null;
    }

    /** Whatever follows "on", "in", "to" or "for". */
    private static String extractObject(String text) {
        Matcher m = Pattern.compile(
            '(?i)\\b(?:on|in|to|for)\\s+(?:the\\s+)?' +
            '([A-Za-z0-9_]{3,60}(?:__c)?)\\b').matcher(text);
        while (m.find()) {
            String candidate = m.group(1);
            if (!(new Set<String>{'order','production','sandbox','it','them','this',
                    'that','avoid','make','ensure','create','update'}
                    .contains(candidate.toLowerCase()))) {
                return candidate;
            }
        }
        return null;
    }

    private static String describe(AIRequestIntent i) {
        List<String> parts = new List<String>{ i.action };
        parts.add(i.targetType == 'Unknown' ? 'component' : 'a ' + label(i.targetType));
        if (String.isNotBlank(i.targetName)) {
            parts.add('named "' + i.targetName + '"');
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
