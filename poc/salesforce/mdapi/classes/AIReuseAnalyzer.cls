/**
 * Turns findings into a recommendation.
 *
 * This is the rule the whole architecture exists to enforce: modify what is
 * already there when it is valid, create new only when it is genuinely
 * needed. Asking for a field that already exists should produce the existing
 * field and a refusal to duplicate it, not a new field.
 */
public with sharing class AIReuseAnalyzer {

    public static final String ALREADY_EXISTS = 'Already Exists';
    public static final String SAFE_TO_CREATE = 'Safe to Create';
    public static final String IMPACT_ASSESSED = 'Impact Assessed';
    public static final String NEEDS_CLARITY = 'Needs Clarification';
    public static final String LIKELY_HANDLED = 'Likely Already Handled';
    public static final String NEEDS_REVIEW = 'Needs Review';

    private static final Set<String> AUTOMATION = new Set<String>{
        'Flow', 'ApexTrigger', 'ApexClass', 'ValidationRule'
    };

    public class Verdict {
        @AuraEnabled public String outcome;
        @AuraEnabled public String headline;
        @AuraEnabled public String detail;
        @AuraEnabled public String recommendation;
        @AuraEnabled public Boolean blocksCreation = false;
        @AuraEnabled public List<String> evidence = new List<String>();
    }

    public static Verdict assess(AIRequestIntent intent,
                                 List<AIContextSlice.Finding> findings) {
        Verdict v = new Verdict();

        if (intent.requestShape == 'Behaviour') {
            return behaviour(v, intent, findings);
        }

        if (intent.action == 'Create') {
            List<AIContextSlice.Finding> exact = exactMatches(intent, findings);
            if (!exact.isEmpty()) {
                return duplicate(v, intent, exact);
            }
            List<AIContextSlice.Finding> near = nearMatches(intent, findings);
            return safeToCreate(v, intent, near, findings);
        }

        if (intent.action == 'Update' || intent.action == 'Delete') {
            return impact(v, intent, findings);
        }

        v.outcome = findings.isEmpty() ? NEEDS_CLARITY : IMPACT_ASSESSED;
        v.headline = findings.isEmpty()
            ? 'Nothing in the Network Services scope matched this request'
            : findings.size() + ' related components found';
        v.detail = findings.isEmpty()
            ? 'Name the object, field or automation you mean and the search can be narrowed.'
            : 'Read-only analysis. No change was requested.';
        v.recommendation = 'Refine the request, or approve to send this context to a model.';
        return v;
    }

    // ------------------------------------------------------------ outcomes

    private static Verdict duplicate(Verdict v, AIRequestIntent intent,
                                     List<AIContextSlice.Finding> exact) {
        AIContextSlice.Finding hit = exact[0];
        v.outcome = ALREADY_EXISTS;
        v.blocksCreation = true;
        v.headline = friendly(intent.targetType) + ' "' + hit.nodeName
                   + '" already exists. Do not create a duplicate.';
        v.detail = 'The request asks to create something that is already in the org. '
                 + 'Creating it again would produce a duplicate, split the data across '
                 + 'two fields and break every report and automation that assumes one.';
        v.recommendation = 'Reuse ' + hit.nodeId + '. If the existing one is genuinely '
                         + 'unfit, reword the request as a change to it rather than a new one.';
        for (AIContextSlice.Finding f : exact) {
            v.evidence.add(f.nodeId + ' · ' + f.provenance);
        }
        return v;
    }

    private static Verdict safeToCreate(Verdict v, AIRequestIntent intent,
                                        List<AIContextSlice.Finding> near,
                                        List<AIContextSlice.Finding> all) {
        v.outcome = SAFE_TO_CREATE;
        v.headline = 'No existing ' + friendly(intent.targetType).toLowerCase()
                   + ' matches "' + (intent.targetName == null ? '?' : intent.targetName)
                   + '". Safe to create.';
        if (near.isEmpty()) {
            v.detail = 'Nothing similar was found in the Network Services scope.';
        } else {
            v.detail = near.size() + ' similarly named component'
                     + (near.size() == 1 ? '' : 's')
                     + ' exist. Check these are not what you meant before creating.';
            for (AIContextSlice.Finding f : near) {
                v.evidence.add(f.nodeId + ' · ' + f.provenance);
            }
        }
        Integer automationCount = countTypes(all, AUTOMATION);
        v.recommendation = automationCount == 0
            ? 'Approve to generate the change.'
            : automationCount + ' automation component'
              + (automationCount == 1 ? '' : 's') + ' on this object will need regression '
              + 'coverage once the change lands.';
        return v;
    }

    private static Verdict impact(Verdict v, AIRequestIntent intent,
                                  List<AIContextSlice.Finding> findings) {
        v.outcome = findings.isEmpty() ? NEEDS_CLARITY : IMPACT_ASSESSED;
        if (findings.isEmpty()) {
            v.headline = 'Nothing matched, so the blast radius cannot be established';
            v.detail = 'A change cannot be assessed against components that were not found.';
            v.recommendation = 'Name the object or component explicitly and search again.';
            return v;
        }
        Integer direct = 0, oneHop = 0, high = 0;
        for (AIContextSlice.Finding f : findings) {
            if (f.impact == 'Direct') { direct++; }
            if (f.impact == 'One Hop') { oneHop++; }
            if (f.riskTier == 'High' || f.riskTier == 'Critical') { high++; }
        }
        v.headline = findings.size() + ' components in the blast radius: '
                   + direct + ' direct, ' + oneHop + ' one hop out';
        v.detail = high == 0
            ? 'Nothing high risk in the affected set.'
            : high + ' of them are high risk and will route to architecture review.';
        v.recommendation = 'Approve to send this bounded context to the model. '
                         + 'Only these ' + findings.size()
                         + ' components go into the prompt, not the whole org.';
        return v;
    }

    /**
     * Behaviour requests cannot be answered by a name lookup.
     *
     * "When an Account is created, create a HealthcareProvider" is not asking
     * whether a component called something exists; it is asking whether the
     * org already does this. So the question becomes: what automation fires on
     * the trigger object, and does any of it touch the objects the request
     * wants written?
     *
     * Crucially this never returns Safe to Create while automation exists on
     * the trigger object. Flow internals are unreadable without the Tooling
     * API, so the honest answer is "these already run, check them", not a
     * clearance the evidence does not support.
     */
    private static Verdict behaviour(Verdict v, AIRequestIntent intent,
                                     List<AIContextSlice.Finding> findings) {
        List<AIContextSlice.Finding> automationHits = new List<AIContextSlice.Finding>();
        List<AIContextSlice.Finding> overlapping = new List<AIContextSlice.Finding>();

        Set<String> affectedLower = new Set<String>();
        for (String o : intent.affectedObjects) {
            affectedLower.add(o.toLowerCase().replaceAll('[^a-z0-9]', ''));
        }

        // A clearance has to be earned. "No automation was found" only means
        // "none exists" if the trigger object was actually in the graph being
        // searched, and the object being absent is exactly what happened when
        // a Flow on Account was reported as nothing at all.
        Boolean sawTriggerObject = false;
        String triggerKey = normalize(intent.triggerObject);

        for (AIContextSlice.Finding f : findings) {
            if (f.nodeType == 'SObject' && triggerKey.length() > 0
                    && (normalize(f.nodeName) == triggerKey
                        || normalize(shortId(f.nodeId)) == triggerKey)) {
                sawTriggerObject = true;
            }
            if (!AUTOMATION.contains(f.nodeType)) {
                continue;
            }
            automationHits.add(f);
            String haystack = ((f.nodeName == null ? '' : f.nodeName) + ' '
                            + (f.relationshipPath == null ? '' : f.relationshipPath))
                            .toLowerCase().replaceAll('[^a-z0-9]', '');
            for (String affected : affectedLower) {
                if (affected.length() > 4 && haystack.contains(affected)) {
                    overlapping.add(f);
                    break;
                }
            }
        }

        String what = intent.affectedObjects.isEmpty()
            ? 'the objects named'
            : String.join(intent.affectedObjects, ' and ');

        if (!overlapping.isEmpty()) {
            v.outcome = LIKELY_HANDLED;
            v.blocksCreation = true;
            v.headline = overlapping.size() + ' existing automation component'
                + (overlapping.size() == 1 ? '' : 's') + ' on ' + intent.triggerObject
                + ' already reference ' + what + '.';
            v.detail = 'This behaviour may already be implemented. Building it '
                + 'again would run the logic twice and create duplicate records.';
            v.recommendation = 'Open these and confirm before building anything new. '
                + 'If one of them is the right place, reword the request as a '
                + 'change to it.';
            for (AIContextSlice.Finding f : overlapping) {
                v.evidence.add(f.nodeId + ' · ' + f.provenance);
            }
            return v;
        }

        if (!automationHits.isEmpty()) {
            v.outcome = NEEDS_REVIEW;
            v.blocksCreation = true;
            v.headline = automationHits.size() + ' automation component'
                + (automationHits.size() == 1 ? '' : 's') + ' already fire on '
                + intent.triggerObject + '.';
            v.detail = 'None of them names ' + what + ', but Flow and Apex '
                + 'internals cannot be read without the Tooling API, so this '
                + 'cannot be cleared from the graph alone. One of these may '
                + 'already do it.';
            v.recommendation = 'Review these before building. Adding another '
                + 'component that fires on the same event risks duplicate '
                + 'records and ordering problems.';
            for (AIContextSlice.Finding f : automationHits) {
                v.evidence.add(f.nodeId + ' · ' + f.provenance);
            }
            return v;
        }

        if (!sawTriggerObject) {
            v.outcome = NEEDS_CLARITY;
            v.blocksCreation = true;
            v.headline = intent.triggerObject + ' is not in the graph, so what '
                + 'already runs on it cannot be established.';
            v.detail = 'The graph is scoped to the pod. This object is not in '
                + 'it, so finding no automation here is not evidence that none '
                + 'exists, and clearing the request on that basis would be a '
                + 'guess dressed up as an answer.';
            v.recommendation = 'Rebuild the graph, or bring ' + intent.triggerObject
                + ' into the pod scope, then ask again.';
            return v;
        }

        v.outcome = SAFE_TO_CREATE;
        v.headline = 'No automation currently fires on ' + intent.triggerObject + '.';
        v.detail = 'Nothing in the graph runs on this event, so there is nothing '
            + 'to duplicate. ' + intent.triggerObject + ' was found in the graph '
            + 'and searched, which is what makes that absence meaningful.';
        v.recommendation = 'Approve to generate the change.';
        return v;
    }

    // ------------------------------------------------------------ matching

    /** Same type, same normalized name. */
    private static List<AIContextSlice.Finding> exactMatches(
            AIRequestIntent intent, List<AIContextSlice.Finding> findings) {
        List<AIContextSlice.Finding> out = new List<AIContextSlice.Finding>();
        if (String.isBlank(intent.targetName)) {
            return out;
        }
        String want = normalize(intent.targetName);
        for (AIContextSlice.Finding f : findings) {
            if (intent.targetType != 'Unknown' && f.nodeType != intent.targetType) {
                continue;
            }
            if (normalize(f.nodeName) == want || normalize(shortId(f.nodeId)) == want) {
                out.add(f);
            }
        }
        return out;
    }

    /** Same type, one name contains the other. */
    private static List<AIContextSlice.Finding> nearMatches(
            AIRequestIntent intent, List<AIContextSlice.Finding> findings) {
        List<AIContextSlice.Finding> out = new List<AIContextSlice.Finding>();
        if (String.isBlank(intent.targetName)) {
            return out;
        }
        String want = normalize(intent.targetName);
        if (want.length() < 3) {
            return out;
        }
        for (AIContextSlice.Finding f : findings) {
            if (intent.targetType != 'Unknown' && f.nodeType != intent.targetType) {
                continue;
            }
            String have = normalize(f.nodeName);
            if (have == want) {
                continue;
            }
            if (have.contains(want) || want.contains(have)) {
                out.add(f);
            }
        }
        return out;
    }

    /** "Provider NPI", "Provider_NPI__c" and "providernpi" all collapse together. */
    @TestVisible
    private static String normalize(String value) {
        if (String.isBlank(value)) {
            return '';
        }
        String s = value.toLowerCase().trim();
        if (s.endsWith('__c')) {
            s = s.substring(0, s.length() - 3);
        }
        return s.replaceAll('[^a-z0-9]', '');
    }

    private static String shortId(String nodeId) {
        if (String.isBlank(nodeId)) {
            return '';
        }
        String s = nodeId.substringAfterLast(':');
        return s.contains('.') ? s.substringAfterLast('.') : s;
    }

    private static Integer countTypes(List<AIContextSlice.Finding> findings,
                                      Set<String> types) {
        Integer n = 0;
        for (AIContextSlice.Finding f : findings) {
            if (types.contains(f.nodeType)) {
                n++;
            }
        }
        return n;
    }

    private static String friendly(String targetType) {
        Map<String, String> m = new Map<String, String>{
            'Field' => 'Field', 'SObject' => 'Object', 'Flow' => 'Flow',
            'ApexClass' => 'Apex class', 'ApexTrigger' => 'Trigger',
            'LightningComponent' => 'Lightning component',
            'ValidationRule' => 'Validation rule', 'RecordType' => 'Record type',
            'Unknown' => 'Component'
        };
        return m.containsKey(targetType) ? m.get(targetType) : targetType;
    }
}
