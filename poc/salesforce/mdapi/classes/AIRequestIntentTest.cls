/**
 * Pins the phrasings that have actually gone wrong in the sandbox.
 *
 * Every case here is a real request typed into the console, not an invented
 * one. The reading the parser produces decides whether the duplicate check
 * fires, so a one-word slip here is the difference between "already exists"
 * and "safe to create" on a field that is sitting in the org.
 */
@IsTest
private class AIRequestIntentTest {

    @IsTest
    static void trailingComponentNounIsNotPartOfTheName() {
        // Screenshot 3: this came back as "effective from date field", which
        // normalises to effectivefromdatefield and never equals the existing
        // Effective_From_Date__c.
        AIRequestIntent i = AIRequestIntent.parse(
            'create effective from date field in healthcarefacility object');

        System.assertEquals('Create', i.action);
        System.assertEquals('Field', i.targetType);
        System.assertEquals('effective from date', i.targetName,
            'The word "field" names the component type, not the field.');
        System.assertEquals('healthcarefacility', i.targetObject);
        System.assertEquals('Date', i.targetDataType);
        System.assertEquals('Component', i.requestShape);
    }

    @IsTest
    static void commaFormPhrasingReadsTheSameName() {
        AIRequestIntent i = AIRequestIntent.parse(
            'create effective from date, date data type field in healthcarefacility object');

        System.assertEquals('effective from date', i.targetName);
        System.assertEquals('Date', i.targetDataType);
        System.assertEquals('healthcarefacility', i.targetObject);
    }

    @IsTest
    static void multiWordNameSurvivesTheWordBeforeTypeNounRule() {
        // The older rule took only the single word in front of "field", so
        // "Provider Tier" was read as "Tier".
        AIRequestIntent i = AIRequestIntent.parse(
            'add a Provider Tier field on HealthcareProvider');

        System.assertEquals('Provider Tier', i.targetName);
        System.assertEquals('HealthcareProvider', i.targetObject);
    }

    @IsTest
    static void quotedAndCalledFormsStillWin() {
        System.assertEquals('Network_Segment__c',
            AIRequestIntent.parse(
                'create a field "Network_Segment__c" on Account').targetName);

        System.assertEquals('Escalation Owner',
            AIRequestIntent.parse(
                'add a lookup field called Escalation Owner on Case').targetName);
    }

    @IsTest
    static void namesAreNeverJustADescriptiveWord() {
        AIRequestIntent i = AIRequestIntent.parse('create a new date field');
        System.assert(String.isBlank(i.targetName),
            'Nothing in that sentence names anything: "' + i.targetName + '"');
    }

    @IsTest
    static void behaviourRequestsCarryNoComponentName() {
        AIRequestIntent i = AIRequestIntent.parse(
            'when account record gets created i want to create a HealthcareProvider '
            + 'and HealthcareFacility record');

        System.assertEquals('Behaviour', i.requestShape);
        System.assertEquals('Created', i.triggerEvent);
        System.assertEquals('account', i.triggerObject.toLowerCase());
        System.assert(String.isBlank(i.targetName),
            'A behaviour has no single component to duplicate-check.');
        System.assert(i.affectedObjects.size() >= 2,
            'Both written objects should be picked up: '
            + String.join(i.affectedObjects, ', '));
    }

    /**
     * The whole point of the name fix: the analyzer must now see the existing
     * field as an exact match and refuse to create a second one.
     */
    @IsTest
    static void existingFieldBlocksCreation() {
        AIRequestIntent i = AIRequestIntent.parse(
            'create effective from date field in healthcarefacility object');

        List<AIContextSlice.Finding> findings = new List<AIContextSlice.Finding>{
            AIContextSlice.build(
                'sf:field:HealthcareFacility.Effective_From_Date__c', 'Field',
                'Effective_From_Date__c', 'HealthcareFacility > field',
                'Existing field', 'Medium', 'SALESFORCE', 'Describe')
        };

        AIReuseAnalyzer.Verdict v = AIReuseAnalyzer.assess(i, findings);

        System.assertEquals(AIReuseAnalyzer.ALREADY_EXISTS, v.outcome, v.headline);
        System.assertEquals(true, v.blocksCreation);
    }
}
