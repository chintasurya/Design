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
        Integer automation = countTypes(all,
            new Set<String>{'Flow', 'ApexTrigger', 'ApexClass', 'ValidationRule'});
        v.recommendation = automation == 0
            ? 'Approve to generate the change.'
            : automation + ' automation component'
              + (automation == 1 ? '' : 's') + ' on this object will need regression '
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
