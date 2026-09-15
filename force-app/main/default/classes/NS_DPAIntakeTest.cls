/*
 *  @Author: Syed Karimulla.
 *  @group: Network services.
 *  @Description: Test class for NS_DPAIntakeTriggerHandler / NS_DPAIntakeHelper.
 *  @created date (mm/dd/yyyy) : 07/13/2026
 *  @last modified date (mm/dd/yyyy): 09/15/2026
 *
 *  ------------------------------------------------------------------------
 *  HOW THIS CLASS STAYS PORTABLE ACROSS ORGS
 *  ------------------------------------------------------------------------
 *  1. ONE conversion chain per test method, and it runs INSIDE
 *     Test.startTest()/stopTest() so it gets the reset governor budget.
 *     DPA records are inserted with a blank Lead_Record_ID__c
 *     (persistWithoutTriggering) so the after-insert trigger does not run
 *     the chain a second time against the un-resettable pre-test budget.
 *
 *  2. No ContentVersion / ContentDocumentLink DML inside a test method.
 *     File fixtures live in @TestSetup, which commits in its own
 *     transaction, so file DML never shares a transaction with the
 *     GCP pub/sub callout.
 *
 *  3. No assertion depends on org metadata:
 *       - multi-select picklist values are compared as Sets, never as a
 *         delimited String (Salesforce normalises the order to the picklist
 *         definition, which differs per org);
 *       - Lead status labels are read from LeadStatus, not hardcoded;
 *       - State/Country fields are never asserted (they return labels when
 *         State & Country picklists are enabled, codes when they are not).
 *
 *  4. testOrgPrerequisites() fails loudly and early when a record type or
 *     the 'Converted' lead status the helper hardcodes is missing, instead
 *     of letting it surface as a confusing cascade further down.
 */
@IsTest
private class NS_DPAIntakeTest {

    /* ===================== CONSTANTS ===================== */

    private static final String BILLING_STATE   = 'CA';
    private static final String BILLING_COUNTRY = 'United States';
    private static final String BILLING_ZIP     = '94965';
    private static final String BILLING_CITY    = 'Sausalito';
    private static final String BILLING_STREET  = '123 Test Street';

    private static final String EMAIL_DOMAIN = '@nsdpa.test';

    // Mirrors of the helper's private role constants.
    private static final String ROLE_PRACTICE_MANAGER = 'Practice Manager';
    private static final String ROLE_CREDENTIALING    = 'Credentialing';
    private static final String ROLE_BILLING          = 'Billing Manager';
    private static final String ROLE_SIGNATORY        = 'Contract-Signature';
    private static final String TYPE_OFFICE_STAFF     = 'Office Staff';

    /* ===================== CALLOUT MOCK ===================== */

    /**
     * HealthcareProviderTriggerHandler calls GCPPubSubPublisher.enqueue()
     * on HealthcareProvider insert/delete, which performs an HttpRequest.
     * Test.setMock() must be active before ANY HealthcareProvider DML.
     */
    private class PubSubMock implements HttpCalloutMock {
        public HttpResponse respond(HttpRequest req) {
            HttpResponse res = new HttpResponse();
            res.setStatusCode(200);
            res.setBody('{"messageIds":["UNIT-TEST"]}');
            return res;
        }
    }

    /* ===================== TEST SETUP ===================== */

    /**
     * Creates every Lead the class needs in a single DML, plus the file
     * fixture used by the Step 6 test.
     *
     * File DML lives here on purpose: @TestSetup runs in its own committed
     * transaction, so ContentVersion / ContentDocumentLink inserts can never
     * share a transaction with the pub/sub callout. That is what produced
     * "System.CalloutException: You have uncommitted work pending" when the
     * file fixture was built inside the test method.
     */
    @TestSetup
    static void setupData() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());

        // Read an open status rather than hardcoding 'Open - Not Contacted',
        // which orgs are free to rename or remove.
        String openStatus = [
            SELECT MasterLabel
            FROM   LeadStatus
            WHERE  IsConverted = false
            ORDER BY SortOrder
            LIMIT 1
        ].MasterLabel;

        List<Lead> leads = new List<Lead>();
        for (String key : new List<String>{
            'trigger', 'triggermixed', 'triggerconverted',
            'bulk1', 'bulk2', 'bulk3',
            'full', 'minimal', 'allno', 'files',
            'addryes', 'addrblank', 'queue', 'preconv',
            'withdpa', 'nodpa',
            'pmyes', 'pmno', 'fmyes', 'nosigdata', 'nocontact'
        }) {
            leads.add(newLead(key, 'Co ' + key, openStatus));
        }

        // 150-char Company drives the HealthcareProvider Name truncation path.
        leads.add(newLead('trunc', 'A'.repeat(150), openStatus));

        insert leads;

        // ---- file fixture for the Step 6 (transferFiles) test ----
        String fileLeadEmail = 'files' + EMAIL_DOMAIN;
        Id fileLeadId = [
            SELECT Id FROM Lead
            WHERE  Email = :fileLeadEmail
            LIMIT 1
        ].Id;

        ContentVersion cv = new ContentVersion(
            Title        = 'Lead Doc',
            PathOnClient = 'LeadDoc.txt',
            VersionData  = Blob.valueOf('Lead Doc Data')
        );
        insert cv;

        insert new ContentDocumentLink(
            ContentDocumentId = [
                SELECT ContentDocumentId FROM ContentVersion WHERE Id = :cv.Id
            ].ContentDocumentId,
            LinkedEntityId = fileLeadId,
            ShareType      = 'V'
        );
    }

    /* ===================== FIXTURE BUILDERS ===================== */

    private static Lead newLead(String key, String company, String status) {
        // FirstName is deliberately NOT one of the Step 10 contact first
        // names (Practice / Facility / Sig / Cred / Bill) so that the
        // converted Contact never collides with an office-staff assertion.
        return new Lead(
            FirstName  = 'Dpa',
            LastName   = key,
            Company    = company,
            Status     = status,
            Email      = key + EMAIL_DOMAIN,
            Phone      = '4151234567',
            Street     = BILLING_STREET, City       = BILLING_CITY,
            State      = BILLING_STATE,  PostalCode = BILLING_ZIP,
            Country    = BILLING_COUNTRY
        );
    }

    private static Lead getLead(String key) {
        String email = key + EMAIL_DOMAIN;
        return [
            SELECT Id, FirstName, LastName, Company, Email, OwnerId
            FROM   Lead
            WHERE  Email = :email
            LIMIT 1
        ];
    }

    private static Account buildNetworkServicesAccount(String name) {
        return new Account(
            Name               = name,
            RecordTypeId       = recordTypeId(Account.SObjectType, 'Network_Services'),
            BillingStreet      = BILLING_STREET, BillingCity        = BILLING_CITY,
            BillingState       = BILLING_STATE,  BillingPostalCode  = BILLING_ZIP,
            BillingCountry     = BILLING_COUNTRY,
            ShippingStreet     = BILLING_STREET, ShippingCity       = BILLING_CITY,
            ShippingState      = BILLING_STATE,  ShippingPostalCode = BILLING_ZIP,
            ShippingCountry    = BILLING_COUNTRY
        );
    }

    /**
     * Creates the shell (parent) Account that satisfies the ParentId lookup
     * filter (Valid_HCP__c = true AND RecordType = Network_Services) and arms
     * NS_DPAIntakeHelper.testShellAccountId with it, so createAccounts()
     * stamps ParentId and the flow skips its own shell-creation branch.
     *
     * Valid_HCP__c is flipped by HealthcareProviderTriggerHandler when a
     * linked HealthcareProvider has TIN_Account__c = true, so the mock must
     * already be installed by the caller.
     */
    private static Id armShell(String name) {
        Account shell = buildNetworkServicesAccount(name);
        insert shell;

        insert new HealthcareProvider(
            Name           = name + ' HP',
            AccountId      = shell.Id,
            RecordTypeId   = recordTypeId(HealthcareProvider.SObjectType, 'Network_Services'),
            TIN_Account__c = true
        );

        Account reloaded = [
            SELECT Id, Valid_HCP__c FROM Account WHERE Id = :shell.Id
        ];
        System.assertEquals(true, reloaded.Valid_HCP__c,
            'Shell Account must end up Valid_HCP__c = true or the ParentId '
            + 'lookup filter rejects every converted Account. Check that '
            + 'HealthcareProviderTriggerHandler is active in this org.');

        NS_DPAIntakeHelper.testShellAccountId = reloaded.Id;
        return reloaded.Id;
    }

    /**
     * Inserts the DPA with a BLANK Lead_Record_ID__c so the after-insert
     * trigger does NOT run the conversion chain, then restores the Lead Id
     * on the IN-MEMORY copy that the test hands to the helper.
     *
     * The helper only ever reads Lead_Record_ID__c off the list passed in -
     * it never re-queries the DPA - so the in-memory value is all it needs.
     *
     * This is the fix for "Too many SOQL queries: 101": previously the
     * pre-startTest insert ran Steps 1-10 in full against the pre-test
     * governor budget (which Test.startTest() cannot reset), and the helper
     * call inside startTest then found the Lead already converted and
     * returned immediately.
     */
    private static void persistWithoutTriggering(NS_DPAIntake_Form__c dpa) {
        String leadRef = dpa.Lead_Record_ID__c;
        dpa.Lead_Record_ID__c = null;
        insert dpa;
        dpa.Lead_Record_ID__c = leadRef;
    }

    private static NS_DPAIntake_Form__c buildFullDpa(Id leadId) {
        return new NS_DPAIntake_Form__c(
            Lead_Record_ID__c                     = String.valueOf(leadId),
            Account_DBA__c                        = 'DBA Test',
            Practice_Phone__c                     = '4151234567',
            Practice_Fax__c                       = '4159876543',
            Practice_Website__c                   = 'https://test.com',
            Billing_Address__Street__s            = BILLING_STREET,
            Billing_Address__City__s              = BILLING_CITY,
            Billing_Address__StateCode__s         = BILLING_STATE,
            Billing_Address__PostalCode__s        = BILLING_ZIP,
            Mailing_Address__Street__s            = BILLING_STREET,
            Mailing_Address__City__s              = BILLING_CITY,
            Mailing_Address__StateCode__s         = BILLING_STATE,
            Mailing_Address__PostalCode__s        = BILLING_ZIP,
            Medicaid_Number__c                    = 111111,
            Medicare_Number__c                    = '222222',
            EHR_System__c                         = 'Epic',
            EHR_Version__c                        = '2024',
            Practice_Management_System__c         = 'Athena',
            Practice_Management_System_Version__c = 'v3',
            CCN__c                                = 'CCN001',
            Do_you_have_Disease_Registry__c       = 'Yes',
            Do_you_outsource_billing__c           = 'No',
            Essential_Community_Provider__c       = 'Yes',
            Credentialing_Email__c                = 'cred@test.com',
            Credentialing_Phone__c                = '4151112222',
            Credentialing_Contact_Name__c         = 'Dr Test',
            Credentialing_Contact_Title__c        = 'MD',
            License_1_Type__c                     = 'MD',
            License_1_Number__c                   = 'LIC001',
            License_1_Issue_Date__c               = Date.today().addYears(-3),
            License_1_Expiration__c               = Date.today().addYears(3),
            State_License_1__c                    = BILLING_STATE,
            Remit_Name__c                         = 'Test Remit',
            ADA_Compliant__c                      = 'Yes',
            VirtualHealthNoProviders__c           = 'Yes',
            Monday_Hours__c                       = '8AM-6PM',
            Tuesday_Hours__c                      = '8AM-6PM',
            Wednesday_Hours__c                    = '8AM-6PM',
            Thursday_Hours__c                     = '8AM-6PM',
            Friday_Hours__c                       = '8AM-4PM',
            Saturday_Hours__c                     = '9AM-1PM',
            Sunday_Hours__c                       = 'Closed',
            Referred_By__c                        = 'Current Patient',
            Join_Interest__c                      = 'Interested',
            Privileges_with_Ascension__c          = 'Yes'
        );
    }

    private static NS_DPAIntake_Form__c buildDpaWithDistinctAddresses(
        Id leadId, String billingDifferentFlag
    ) {
        return new NS_DPAIntake_Form__c(
            Lead_Record_ID__c              = String.valueOf(leadId),
            Billing_Address_Different__c   = billingDifferentFlag,
            Billing_Address__Street__s     = '123 Billing St',
            Billing_Address__City__s       = 'Chicago',
            Billing_Address__StateCode__s  = 'IL',
            Billing_Address__PostalCode__s = '60601',
            Mailing_Address__Street__s     = '456 Mailing Ave',
            Mailing_Address__City__s       = 'Springfield',
            Mailing_Address__StateCode__s  = 'IL',
            Mailing_Address__PostalCode__s = '62704'
        );
    }

    private static NS_DPAIntake_Form__c buildDpaWithContacts(
        Id leadId, Boolean usePmPath, String contractSignatoryFlag
    ) {
        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c     = String.valueOf(leadId),
            Contract_Signatory__c = contractSignatoryFlag,

            CS_First_Name__c = 'Sig',
            CS_Last_Name__c  = 'Natory',
            CS_Phone__c      = '4155551111',
            CS_Email__c      = 'sig@test.com',
            CS_Role__c       = ROLE_CREDENTIALING,

            CC_First_Name__c       = 'Cred',
            CC_Last_Name__c        = 'Entialing',
            Credentialing_Phone__c = '4155552222',
            Credentialing_Email__c = 'cc@test.com',

            BC_First_Name__c = 'Bill',
            BC_Last_Name__c  = 'Ing',
            BC_Phone__c      = '4155553333',
            Billing_Email__c = 'bc@test.com'
        );

        if (usePmPath) {
            dpa.PM_First_Name__c  = 'Practice';
            dpa.PM_Last_Name__c   = 'Manager';
            dpa.Practice_Phone__c = '4155554444';
            dpa.Practice_Email__c = 'pm@test.com';
        } else {
            dpa.FM_First_Name__c = 'Facility';
            dpa.FM_Last_Name__c  = 'Manager';
            dpa.FM_Phone__c      = '4155555555';
            dpa.FM_Email__c      = 'fm@test.com';
        }
        return dpa;
    }

    /* ===================== ASSERTION HELPERS ===================== */

    private static Id recordTypeId(Schema.SObjectType objType, String devName) {
        Map<String, Schema.RecordTypeInfo> rtMap =
            objType.getDescribe().getRecordTypeInfosByDeveloperName();
        System.assert(rtMap.containsKey(devName),
            'Missing record type ' + devName + ' on ' + objType
            + '. NS_DPAIntakeHelper depends on it.');
        return rtMap.get(devName).getRecordTypeId();
    }

    /**
     * Multi-select picklist values are stored in the ORDER DEFINED ON THE
     * FIELD, not the order the code concatenated them, so comparing the raw
     * String couples the test to field metadata. Compare Sets instead.
     */
    private static Set<String> rolesOf(String roles) {
        Set<String> out = new Set<String>();
        if (String.isNotBlank(roles)) {
            for (String r : roles.split(';')) {
                out.add(r.trim());
            }
        }
        return out;
    }

    private static Lead convertedLead(Id leadId) {
        return [
            SELECT Id, IsConverted, ConvertedAccountId,
                   ConvertedContactId, ConvertedOpportunityId
            FROM   Lead
            WHERE  Id = :leadId
        ];
    }

    private static Map<String, AccountContactRelation> officeStaffAcrs(Id accountId) {
        Map<String, AccountContactRelation> byFirstName =
            new Map<String, AccountContactRelation>();
        for (AccountContactRelation acr : [
            SELECT Id, Roles, IsActive, StartDate,
                   Contact.FirstName, Contact.LastName,
                   Contact.Phone, Contact.Email, Contact.Type__c
            FROM   AccountContactRelation
            WHERE  AccountId = :accountId
            AND    Contact.Type__c = :TYPE_OFFICE_STAFF
        ]) {
            byFirstName.put(acr.Contact.FirstName, acr);
        }
        return byFirstName;
    }

    /* ===================== ORG PREREQUISITES ===================== */

    /**
     * Fails fast, with a readable message, when the org is missing metadata
     * NS_DPAIntakeHelper hardcodes. Without this an org that lacks a record
     * type just gets RecordTypeId = null (the helper logs a warning and
     * carries on), and the real cause surfaces much later as an unrelated
     * assertion failure.
     */
    @IsTest
    static void testOrgPrerequisites() {
        System.assertNotEquals(null,
            recordTypeId(Account.SObjectType, 'IndustriesBusiness'),
            'Account.IndustriesBusiness record type is required');
        System.assertNotEquals(null,
            recordTypeId(Contact.SObjectType, 'IndustriesBusiness'),
            'Contact.IndustriesBusiness record type is required');
        System.assertNotEquals(null,
            recordTypeId(Opportunity.SObjectType, 'Network_Services'),
            'Opportunity.Network_Services record type is required');
        System.assertNotEquals(null,
            recordTypeId(Account.SObjectType, 'Network_Services'),
            'Account.Network_Services record type is required for the shell');
        System.assertNotEquals(null,
            recordTypeId(HealthcareProvider.SObjectType, 'Network_Services'),
            'HealthcareProvider.Network_Services record type is required');

        // NS_DPAIntakeHelper.CONVERTED_STATUS is the literal 'Converted'.
        List<LeadStatus> converted = [
            SELECT MasterLabel FROM LeadStatus
            WHERE  IsConverted = true AND MasterLabel = 'Converted'
        ];
        System.assertEquals(false, converted.isEmpty(),
            'NS_DPAIntakeHelper hardcodes the converted status label '
            + '"Converted"; this org has no such LeadStatus, so every '
            + 'Database.convertLead call will fail.');
    }

    /* ===================== TRIGGER ENTRY POINT ===================== */

    @IsTest
    static void testTriggerConvertsLead() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        Id shellId = armShell('Trigger Shell');
        Lead ld = getLead('trigger');

        Test.startTest();
        insert new NS_DPAIntake_Form__c(
            Lead_Record_ID__c = String.valueOf(ld.Id)
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals(true, conv.IsConverted,
            'Inserting a DPA with a valid Lead_Record_ID__c must convert the Lead');
        System.assertNotEquals(null, conv.ConvertedAccountId, 'Account expected');
        System.assertNotEquals(null, conv.ConvertedContactId, 'Contact expected');
        System.assertNotEquals(null, conv.ConvertedOpportunityId, 'Opportunity expected');

        Account acc = [
            SELECT ParentId, RecordTypeId FROM Account WHERE Id = :conv.ConvertedAccountId
        ];
        System.assertEquals(shellId, acc.ParentId,
            'Converted Account should be parented to the shell');
        System.assertEquals(
            recordTypeId(Account.SObjectType, 'IndustriesBusiness'),
            acc.RecordTypeId,
            'Converted Account should use the IndustriesBusiness record type');
    }

    @IsTest
    static void testTriggerBlankLeadId() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());

        Test.startTest();
        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c();
        insert dpa;
        Test.stopTest();

        System.assertNotEquals(null, dpa.Id,
            'A DPA with no Lead_Record_ID__c must still save');
        System.assertEquals(0, [SELECT COUNT() FROM Lead WHERE IsConverted = true],
            'A blank Lead_Record_ID__c must not convert anything');
    }

    @IsTest
    static void testTriggerInvalidLeadId() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());

        Test.startTest();
        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c = 'INVALID_ID'
        );
        insert dpa;
        Test.stopTest();

        System.assertNotEquals(null, dpa.Id,
            'An unparseable Lead_Record_ID__c must be caught and logged, not thrown');
        System.assertEquals(0, [SELECT COUNT() FROM Lead WHERE IsConverted = true],
            'An unparseable Lead_Record_ID__c must not convert anything');
    }

    @IsTest
    static void testTriggerMixedBatchSkipsBlanks() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Mixed Shell');
        Lead ld = getLead('triggermixed');

        Test.startTest();
        insert new List<NS_DPAIntake_Form__c>{
            new NS_DPAIntake_Form__c(),
            new NS_DPAIntake_Form__c(Lead_Record_ID__c = 'INVALID_ID'),
            new NS_DPAIntake_Form__c(Lead_Record_ID__c = String.valueOf(ld.Id))
        };
        Test.stopTest();

        System.assertEquals(true, convertedLead(ld.Id).IsConverted,
            'The valid row in a mixed batch must still convert');
        System.assertEquals(1, [SELECT COUNT() FROM Lead WHERE IsConverted = true],
            'Only the valid row should have converted');
    }

    @IsTest
    static void testTriggerAlreadyConvertedLeadIsSkipped() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Preconverted Trigger Shell');
        Lead ld = getLead('triggerconverted');

        Test.startTest();
        Database.LeadConvert lc = new Database.LeadConvert();
        lc.setLeadId(ld.Id);
        lc.setConvertedStatus(convertedStatusLabel());
        Database.convertLead(lc);

        // DPA arrives after the Lead was converted by some other route.
        insert new NS_DPAIntake_Form__c(
            Lead_Record_ID__c = String.valueOf(ld.Id)
        );
        Test.stopTest();

        System.assertEquals(1,
            [SELECT COUNT() FROM Account WHERE Name = :ld.Company],
            'An already-converted Lead must not get a second Account');
    }

    @IsTest
    static void testTriggerBulk() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Bulk Shell');

        Set<String> bulkEmails = new Set<String>{
            'bulk1' + EMAIL_DOMAIN,
            'bulk2' + EMAIL_DOMAIN,
            'bulk3' + EMAIL_DOMAIN
        };
        List<Lead> leads = [
            SELECT Id FROM Lead WHERE Email IN :bulkEmails
        ];
        System.assertEquals(3, leads.size(), 'Expected 3 bulk leads from @TestSetup');

        List<NS_DPAIntake_Form__c> dpas = new List<NS_DPAIntake_Form__c>();
        for (Lead ld : leads) {
            dpas.add(new NS_DPAIntake_Form__c(
                Lead_Record_ID__c = String.valueOf(ld.Id)
            ));
        }

        Test.startTest();
        insert dpas;
        Test.stopTest();

        System.assertEquals(3,
            [SELECT COUNT() FROM Lead WHERE Id IN :leads AND IsConverted = true],
            'All three Leads in the batch should convert in one transaction');
    }

    private static String convertedStatusLabel() {
        return [
            SELECT MasterLabel FROM LeadStatus
            WHERE  IsConverted = true
            ORDER BY SortOrder
            LIMIT 1
        ].MasterLabel;
    }

    /* ===================== HANDLER PLUMBING ===================== */

    @IsTest
    static void testHandlerNullAndEmptyItems() {
        NS_DPAIntakeTriggerHandler h = new NS_DPAIntakeTriggerHandler();

        Test.startTest();
        h.afterInsert(null, null);
        h.afterInsert(new List<SObject>(), new Map<Id, SObject>());
        Test.stopTest();

        System.assertEquals('NS_DPAIntake_Form__c', h.getName(),
            'getName() should return the object API name');
    }

    @IsTest
    static void testHandlerUnusedOverrides() {
        NS_DPAIntakeTriggerHandler h = new NS_DPAIntakeTriggerHandler();
        Map<Id, SObject> em = new Map<Id, SObject>();
        List<SObject>    el = new List<SObject>();

        Test.startTest();
        h.beforeInsert(el);
        h.beforeUpdate(el, em, em);
        h.beforeDelete(em);
        h.afterUpdate(el, em, em);
        h.afterDelete(em);
        h.afterUndelete(em);
        Test.stopTest();

        // The overrides are intentional no-ops; proving they do not touch
        // data is the only meaningful assertion available.
        System.assertEquals(0, [SELECT COUNT() FROM Lead WHERE IsConverted = true],
            'Unused handler overrides must not perform any DML');
    }

    @IsTest
    static void testHelperEmptyLeadSet() {
        Integer accountsBefore = [SELECT COUNT() FROM Account];

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>(), new List<NS_DPAIntake_Form__c>()
        );
        Test.stopTest();

        System.assertEquals(accountsBefore, [SELECT COUNT() FROM Account],
            'An empty lead set must return before creating anything');
    }

    @IsTest
    static void testHelperInvalidLeadIdIsCaught() {
        Integer accountsBefore = [SELECT COUNT() FROM Account];

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>(),
            new List<NS_DPAIntake_Form__c>{
                new NS_DPAIntake_Form__c(Lead_Record_ID__c = 'NOT_A_VALID_ID')
            }
        );
        Test.stopTest();

        System.assertEquals(accountsBefore, [SELECT COUNT() FROM Account],
            'An unparseable Lead_Record_ID__c must be swallowed, not thrown');
    }

    /* ===================== HELPER: FULL MAPPING ===================== */

    /**
     * Covers Steps 1-5 and Step 9 with hard assertions, and Step 10's
     * "no contact-role data" skip.
     *
     * Note: BillingState / ShippingState are deliberately not asserted -
     * they return the state LABEL when State & Country picklists are enabled
     * and the CODE when they are not, so any assertion on them is org
     * configuration, not behaviour.
     */
    @IsTest
    static void testFullDpaMapsAccountContactAndOpportunity() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        Id shellId = armShell('Full Shell');
        Lead ld = getLead('full');

        DateTime appt = DateTime.newInstance(2026, 10, 1, 9, 0, 0);
        NS_DPAIntake_Form__c dpa = buildFullDpa(ld.Id);
        dpa.X3rd_Next_Available_Appointment__c = appt;
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals(true, conv.IsConverted, 'Lead should be converted');

        // ---- Step 1 + Step 5 : Account ----
        Account acc = [
            SELECT Name, ParentId, RecordTypeId, Account_DBA__c,
                   BillingStreet, BillingCity, BillingPostalCode,
                   ShippingStreet, ShippingCity, ShippingPostalCode,
                   Phone, Fax, Website
            FROM   Account WHERE Id = :conv.ConvertedAccountId
        ];
        System.assertEquals(ld.Company, acc.Name,
            'Account Name should come from Lead.Company');
        System.assertEquals(shellId, acc.ParentId, 'ParentId should be the shell');
        System.assertEquals('DBA Test', acc.Account_DBA__c, 'Account_DBA__c mapping');
        System.assertEquals(BILLING_STREET, acc.BillingStreet, 'BillingStreet mapping');
        System.assertEquals(BILLING_CITY, acc.BillingCity, 'BillingCity mapping');
        System.assertEquals(BILLING_ZIP, acc.BillingPostalCode, 'BillingPostalCode mapping');
        System.assertEquals(BILLING_STREET, acc.ShippingStreet, 'ShippingStreet mapping');
        System.assertEquals(BILLING_CITY, acc.ShippingCity, 'ShippingCity mapping');
        System.assertEquals(BILLING_ZIP, acc.ShippingPostalCode, 'ShippingPostalCode mapping');
        System.assertEquals('4151234567', acc.Phone, 'Practice_Phone__c -> Phone');
        System.assertEquals('4159876543', acc.Fax, 'Practice_Fax__c -> Fax');
        System.assertEquals('https://test.com', acc.Website, 'Practice_Website__c -> Website');

        // ---- Step 2 : Contact ----
        Contact con = [
            SELECT FirstName, LastName, Email, Phone, AccountId, RecordTypeId
            FROM   Contact WHERE Id = :conv.ConvertedContactId
        ];
        System.assertEquals(ld.FirstName, con.FirstName, 'Contact FirstName from Lead');
        System.assertEquals(ld.LastName, con.LastName, 'Contact LastName from Lead');
        System.assertEquals(conv.ConvertedAccountId, con.AccountId,
            'Contact should hang off the converted Account');
        System.assertEquals(
            recordTypeId(Contact.SObjectType, 'IndustriesBusiness'),
            con.RecordTypeId, 'Contact record type');

        // ---- Step 4 + Step 9 : Opportunity ----
        Opportunity opp = [
            SELECT RecordTypeId, Referred_By__c, Join_Interest__c,
                   X3rd_Next_Available_Appointment__c,
                   Privileges_with_Ascension__c
            FROM   Opportunity WHERE Id = :conv.ConvertedOpportunityId
        ];
        System.assertEquals(
            recordTypeId(Opportunity.SObjectType, 'Network_Services'),
            opp.RecordTypeId, 'Step 4 should restamp the Opportunity record type');
        System.assertEquals(new Set<String>{ 'Current Patient' },
            rolesOf(opp.Referred_By__c),
            'Referred_By__c mapping (compared as a Set - multi-select order '
            + 'is normalised to the picklist definition)');
        System.assertEquals('Interested', opp.Join_Interest__c, 'Join_Interest__c mapping');
        System.assertEquals(appt, opp.X3rd_Next_Available_Appointment__c,
            'X3rd_Next_Available_Appointment__c mapping');
        System.assertEquals('Y', opp.Privileges_with_Ascension__c,
            'Privileges_with_Ascension__c Yes should map to Y');

        // ---- Step 10 : nothing to do, no PM/FM/CC/BC data on this DPA ----
        System.assertEquals(0, officeStaffAcrs(conv.ConvertedAccountId).size(),
            'A DPA with no PM/FM/CC/BC data must not create office-staff Contacts');
    }

    @IsTest
    static void testMinimalDpaLeavesAccountFieldsUntouched() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Minimal Shell');
        Lead ld = getLead('minimal');

        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c = String.valueOf(ld.Id)
        );
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals(true, conv.IsConverted, 'Lead should still convert');

        Account acc = [
            SELECT Account_DBA__c, Phone, Fax, Website, BillingStreet
            FROM   Account WHERE Id = :conv.ConvertedAccountId
        ];
        System.assertEquals(null, acc.Account_DBA__c,
            'Step 5 must skip blank DPA fields rather than null out the Account');
        System.assertEquals(null, acc.Fax, 'Blank Practice_Fax__c must be skipped');
        System.assertEquals(null, acc.Website, 'Blank Practice_Website__c must be skipped');
        System.assertEquals(BILLING_STREET, acc.BillingStreet,
            'BillingStreet should still hold the value copied from the Lead');
    }

    @IsTest
    static void testAllNoBranches() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('No Branch Shell');
        Lead ld = getLead('allno');

        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c               = String.valueOf(ld.Id),
            Privileges_with_Ascension__c    = 'No',
            ADA_Compliant__c                = 'No',
            VirtualHealthNoProviders__c     = 'No',
            Do_you_have_Disease_Registry__c = 'No',
            Do_you_outsource_billing__c     = 'Yes',
            Essential_Community_Provider__c = 'No'
        );
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals('N', [
            SELECT Privileges_with_Ascension__c FROM Opportunity
            WHERE  Id = :conv.ConvertedOpportunityId
        ].Privileges_with_Ascension__c,
            'Privileges_with_Ascension__c No should map to N');

        // Step 7/8 picklist-to-checkbox conversions are asserted here only
        // when this org's automation actually created the HP/HF records -
        // see testHealthcareProviderAndFacilityMapping for the rationale.
        for (HealthcareProvider hp : [
            SELECT Do_you_have_a_Disease_Registry__c, Do_you_outsource_billing__c,
                   Essential_Community_Provider__c
            FROM   HealthcareProvider WHERE AccountId = :conv.ConvertedAccountId
        ]) {
            System.assertEquals(false, hp.Do_you_have_a_Disease_Registry__c,
                'Disease registry No -> false');
            System.assertEquals(true, hp.Do_you_outsource_billing__c,
                'Outsource billing Yes -> true');
            System.assertEquals(false, hp.Essential_Community_Provider__c,
                'Essential community provider No -> false');
        }
        for (HealthcareFacility hf : [
            SELECT ADA_Compliant__c, VirtualHealthNoProviders__c
            FROM   HealthcareFacility WHERE AccountId = :conv.ConvertedAccountId
        ]) {
            System.assertEquals('N', hf.ADA_Compliant__c, 'ADA_Compliant__c No -> N');
            System.assertEquals('N', hf.VirtualHealthNoProviders__c,
                'VirtualHealthNoProviders__c No -> N');
        }
    }

    /**
     * Lead.Company is required in a stock org, so this Lead is built inside
     * the test method rather than @TestSetup: if an org rejects a blank
     * Company only this one test fails, instead of the whole class.
     */
    @IsTest
    static void testLeadWithoutCompanyUsesLastName() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('NoCompany Shell');

        Lead ld = new Lead(
            FirstName  = 'Dpa', LastName = 'NoCompany',
            Status     = [
                SELECT MasterLabel FROM LeadStatus
                WHERE  IsConverted = false ORDER BY SortOrder LIMIT 1
            ].MasterLabel,
            Street     = BILLING_STREET, City       = BILLING_CITY,
            State      = BILLING_STATE,  PostalCode = BILLING_ZIP,
            Country    = BILLING_COUNTRY
        );
        insert ld;

        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c = String.valueOf(ld.Id)
        );
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals('NoCompany',
            [SELECT Name FROM Account WHERE Id = :conv.ConvertedAccountId].Name,
            'A blank Company must fall back to LastName for the Account Name');
        System.assertEquals('NoCompany',
            [SELECT Name FROM Opportunity WHERE Id = :conv.ConvertedOpportunityId].Name,
            'A blank Company must fall back to LastName for the Opportunity Name');
    }

    /* ===================== HELPER: ADDRESS MAPPING ===================== */

    /**
     * updateAccountsFromDpa copies Billing_Address__* -> Billing* and
     * Mailing_Address__* -> Shipping* UNCONDITIONALLY; it never reads
     * Billing_Address_Different__c. These two tests therefore assert the
     * SAME mapping for 'Yes' and for a blank flag, which is what the code
     * currently does.
     *
     * If the requirement is "when the flag is No/blank, copy the mailing
     * address into both address blocks", that branch is missing from
     * NS_DPAIntakeHelper - it is a helper change, not a test change.
     */
    @IsTest
    static void testAddressMappingFlagYes() {
        assertAddressMapping('addryes', 'Addr Yes Shell', 'Yes');
    }

    @IsTest
    static void testAddressMappingFlagBlank() {
        assertAddressMapping('addrblank', 'Addr Blank Shell', null);
    }

    private static void assertAddressMapping(
        String leadKey, String shellName, String flag
    ) {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell(shellName);
        Lead ld = getLead(leadKey);

        NS_DPAIntake_Form__c dpa = buildDpaWithDistinctAddresses(ld.Id, flag);
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertNotEquals(null, conv.ConvertedAccountId,
            'Conversion must succeed before the address mapping can be checked');

        Account acc = [
            SELECT BillingStreet, BillingCity, BillingPostalCode,
                   ShippingStreet, ShippingCity, ShippingPostalCode
            FROM   Account WHERE Id = :conv.ConvertedAccountId
        ];
        System.assertEquals('123 Billing St', acc.BillingStreet,
            'BillingStreet must come from Billing_Address__Street__s');
        System.assertEquals('Chicago', acc.BillingCity, 'BillingCity mapping');
        System.assertEquals('60601', acc.BillingPostalCode, 'BillingPostalCode mapping');
        System.assertEquals('456 Mailing Ave', acc.ShippingStreet,
            'ShippingStreet must come from Mailing_Address__Street__s');
        System.assertEquals('Springfield', acc.ShippingCity, 'ShippingCity mapping');
        System.assertEquals('62704', acc.ShippingPostalCode, 'ShippingPostalCode mapping');
    }

    /* ===================== HELPER: FILES (STEP 6) ===================== */

    /**
     * The ContentVersion / ContentDocumentLink fixture is built in
     * @TestSetup, never here - building it inside the test method is what
     * produced "System.CalloutException: You have uncommitted work pending"
     * when the pub/sub Queueable ran. The shell (and therefore the
     * HealthcareProvider insert that enqueues that Queueable) is created
     * INSIDE the start/stop block so the async job is collected and executed
     * after Test.stopTest() in its own transaction.
     */
    @IsTest
    static void testFilesAreLinkedToOpportunity() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        Lead ld = getLead('files');

        Id leadDocId = [
            SELECT ContentDocumentId FROM ContentDocumentLink
            WHERE  LinkedEntityId = :ld.Id
            LIMIT 1
        ].ContentDocumentId;

        Test.startTest();
        armShell('Files Shell');

        NS_DPAIntake_Form__c dpa = buildFullDpa(ld.Id);
        persistWithoutTriggering(dpa);

        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertNotEquals(null, conv.ConvertedOpportunityId,
            'Opportunity is required before files can be relinked');

        Set<Id> oppDocIds = new Set<Id>();
        for (ContentDocumentLink cdl : [
            SELECT ContentDocumentId FROM ContentDocumentLink
            WHERE  LinkedEntityId = :conv.ConvertedOpportunityId
        ]) {
            oppDocIds.add(cdl.ContentDocumentId);
        }
        System.assertEquals(true, oppDocIds.contains(leadDocId),
            'Step 6 must relink the Lead file to the converted Opportunity');
    }

    /* ===================== HELPER: HP / HF (STEPS 7-8) ===================== */

    /**
     * Steps 7 and 8 only do work when a HealthcareProvider /
     * HealthcareFacility already exists for the converted Account, and
     * nothing in NS_DPAIntakeHelper creates them - that is declarative
     * automation. So the mapping assertions run only when the records are
     * present, while the conversion itself is asserted unconditionally.
     *
     * KNOWN COVERAGE GAP: in an org where no automation creates HP/HF for a
     * converted Account, the bodies of updateHealthcareProviderFromDpa and
     * updateHealthcareFacilityFromDpa are never executed by this class.
     * Covering them deterministically needs a seam in the helper (for
     * example an @TestVisible hook, like the existing testShellAccountId).
     */
    @IsTest
    static void testHealthcareProviderAndFacilityMapping() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Trunc Shell');
        Lead ld = getLead('trunc');   // 150-char Company

        NS_DPAIntake_Form__c dpa = buildFullDpa(ld.Id);
        dpa.Billing_Address__Street__s = 'B'.repeat(150);
        dpa.Mailing_Address__Street__s = 'B'.repeat(150);
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals(true, conv.IsConverted,
            'A 150-character Company and 150-character street must not break conversion');

        for (HealthcareProvider hp : [
            SELECT Name, TIN__c, EhrSystem, EHR_Version__c, CCN__c,
                   Medicare_Number__c, Medicaid_Number__c,
                   Do_you_have_a_Disease_Registry__c,
                   Do_you_outsource_billing__c,
                   Essential_Community_Provider__c,
                   Practice_Management_System__c
            FROM   HealthcareProvider WHERE AccountId = :conv.ConvertedAccountId
        ]) {
            System.assertEquals(true,
                hp.Name.startsWith('A'.repeat(112) + '...'),
                'Names longer than 115 chars must be truncated to left(112) + "..."');
            System.assertEquals('Epic', hp.EhrSystem, 'EHR_System__c -> EhrSystem');
            System.assertEquals('2024', hp.EHR_Version__c, 'EHR_Version__c mapping');
            System.assertEquals('CCN001', hp.CCN__c, 'CCN__c mapping');
            System.assertEquals('222222', hp.Medicare_Number__c, 'Medicare_Number__c mapping');
            System.assertEquals('Athena', hp.Practice_Management_System__c,
                'Practice_Management_System__c mapping');
            System.assertEquals(true, hp.Do_you_have_a_Disease_Registry__c,
                'Disease registry Yes -> true');
            System.assertEquals(false, hp.Do_you_outsource_billing__c,
                'Outsource billing No -> false');
            System.assertEquals(true, hp.Essential_Community_Provider__c,
                'Essential community provider Yes -> true');
        }

        for (HealthcareFacility hf : [
            SELECT Credentialing_Email__c, Credentialing_Phone__c,
                   Credentialing_Contact_Name__c, Credentialing_Contact_Title__c,
                   CMS_Certification_Number__c, License_1_Number__c,
                   License_1_Type__c, Remit_Name__c,
                   Monday_Hours__c, Sunday_Hours__c,
                   ADA_Compliant__c, VirtualHealthNoProviders__c
            FROM   HealthcareFacility WHERE AccountId = :conv.ConvertedAccountId
        ]) {
            System.assertEquals('cred@test.com', hf.Credentialing_Email__c,
                'Credentialing_Email__c mapping');
            System.assertEquals('Dr Test', hf.Credentialing_Contact_Name__c,
                'Credentialing_Contact_Name__c mapping');
            System.assertEquals('CCN001', hf.CMS_Certification_Number__c,
                'CCN__c -> CMS_Certification_Number__c');
            System.assertEquals('LIC001', hf.License_1_Number__c, 'License_1_Number__c mapping');
            System.assertEquals('Test Remit', hf.Remit_Name__c, 'Remit_Name__c mapping');
            System.assertEquals('8AM-6PM', hf.Monday_Hours__c, 'Monday_Hours__c mapping');
            System.assertEquals('Closed', hf.Sunday_Hours__c, 'Sunday_Hours__c mapping');
            System.assertEquals('Y', hf.ADA_Compliant__c, 'ADA_Compliant__c Yes -> Y');
            System.assertEquals('Y', hf.VirtualHealthNoProviders__c,
                'VirtualHealthNoProviders__c Yes -> Y');
        }
    }

    /* ===================== HELPER: EDGE CASES ===================== */

    @IsTest
    static void testAlreadyConvertedLeadReturnsEarly() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Preconverted Shell');
        Lead ld = getLead('preconv');

        Test.startTest();
        Database.LeadConvert lc = new Database.LeadConvert();
        lc.setLeadId(ld.Id);
        lc.setConvertedStatus(convertedStatusLabel());
        Database.convertLead(lc);

        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id },
            new List<NS_DPAIntake_Form__c>{
                new NS_DPAIntake_Form__c(Lead_Record_ID__c = String.valueOf(ld.Id))
            }
        );
        Test.stopTest();

        System.assertEquals(true, convertedLead(ld.Id).IsConverted,
            'Lead should already be converted');
        System.assertEquals(1, [SELECT COUNT() FROM Account WHERE Name = :ld.Company],
            'processLeadConversion must not create a second Account for a '
            + 'Lead that is already converted');
    }

    @IsTest
    static void testLeadWithoutDpaStillConvertsButIsNotMapped() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('NoDpa Shell');

        Lead withDpa = getLead('withdpa');
        Lead noDpa   = getLead('nodpa');

        NS_DPAIntake_Form__c dpa = buildFullDpa(withDpa.Id);
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ withDpa.Id, noDpa.Id },
            new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead convWith = convertedLead(withDpa.Id);
        Lead convNo   = convertedLead(noDpa.Id);
        System.assertEquals(true, convWith.IsConverted, 'Lead with a DPA should convert');
        System.assertEquals(true, convNo.IsConverted,
            'Steps 1-4 do not depend on a DPA, so this Lead should convert too');

        System.assertEquals('DBA Test',
            [SELECT Account_DBA__c FROM Account WHERE Id = :convWith.ConvertedAccountId]
                .Account_DBA__c,
            'The Lead with a DPA should get its Account fields mapped');
        System.assertEquals(null,
            [SELECT Account_DBA__c FROM Account WHERE Id = :convNo.ConvertedAccountId]
                .Account_DBA__c,
            'The Lead with no DPA must be skipped by Step 5, not mapped from '
            + 'a different Lead DPA');
    }

    @IsTest
    static void testQueueOwnedLeadFallsBackToRunningUser() {
        // Group is a setup object: System.runAs keeps this out of a
        // MIXED_DML_OPERATION with the Account/Contact DML below.
        Group q = new Group(Name = 'Test Lead Queue', Type = 'Queue');
        System.runAs(new User(Id = UserInfo.getUserId())) {
            insert q;
            insert new QueueSobject(QueueId = q.Id, SobjectType = 'Lead');
        }

        Lead ld = getLead('queue');
        update new Lead(Id = ld.Id, OwnerId = q.Id);

        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Queue Shell');

        NS_DPAIntake_Form__c dpa = buildFullDpa(ld.Id);
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals(true, conv.IsConverted,
            'A queue-owned Lead must still convert');
        System.assertEquals(UserInfo.getUserId(),
            [SELECT OwnerId FROM Opportunity WHERE Id = :conv.ConvertedOpportunityId]
                .OwnerId,
            'A queue OwnerId is not a User, so convertLeads must fall back to '
            + 'UserInfo.getUserId()');
    }

    /* ===================== HELPER: STEP 10 CONTACTS / ACRs ===================== */

    @IsTest
    static void testStep10PracticeManagerIsAlsoSignatory() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Step10 PM Yes Shell');
        Lead ld = getLead('pmyes');

        NS_DPAIntake_Form__c dpa = buildDpaWithContacts(ld.Id, true, 'Yes');
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertNotEquals(null, conv.ConvertedAccountId, 'Account expected');

        Map<String, AccountContactRelation> acrs = officeStaffAcrs(conv.ConvertedAccountId);
        System.assertEquals(3, acrs.size(),
            'Expected 3 office-staff Contacts: PM (also signatory), '
            + 'Credentialing, Billing. Found: ' + acrs.keySet());

        System.assertEquals(
            new Set<String>{ ROLE_PRACTICE_MANAGER, ROLE_SIGNATORY },
            rolesOf(acrs.get('Practice').Roles),
            'A PM who is also the signatory should carry both roles on one ACR');
        System.assertEquals(new Set<String>{ ROLE_CREDENTIALING },
            rolesOf(acrs.get('Cred').Roles), 'Credentialing contact role');
        System.assertEquals(new Set<String>{ ROLE_BILLING },
            rolesOf(acrs.get('Bill').Roles), 'Billing contact role');

        // Contact + ACR field mapping
        AccountContactRelation pm = acrs.get('Practice');
        System.assertEquals('Manager', pm.Contact.LastName, 'PM_Last_Name__c mapping');
        System.assertEquals('4155554444', pm.Contact.Phone, 'Practice_Phone__c mapping');
        System.assertEquals('pm@test.com', pm.Contact.Email, 'Practice_Email__c mapping');
        System.assertEquals(TYPE_OFFICE_STAFF, pm.Contact.Type__c, 'Contact Type__c');
        System.assertEquals(true, pm.IsActive, 'ACR should be activated');
        System.assertEquals(Date.today(), pm.StartDate,
            'StartDate falls back to Date.today() when the DPA has no CreatedDate '
            + 'on the in-memory record handed to the helper');
    }

    @IsTest
    static void testStep10SeparateSignatory() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Step10 PM No Shell');
        Lead ld = getLead('pmno');

        NS_DPAIntake_Form__c dpa = buildDpaWithContacts(ld.Id, true, 'No');
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Map<String, AccountContactRelation> acrs =
            officeStaffAcrs(convertedLead(ld.Id).ConvertedAccountId);
        System.assertEquals(4, acrs.size(),
            'Expected 4 office-staff Contacts: PM, separate Signatory, '
            + 'Credentialing, Billing. Found: ' + acrs.keySet());

        System.assertEquals(new Set<String>{ ROLE_PRACTICE_MANAGER },
            rolesOf(acrs.get('Practice').Roles),
            'A PM who is not the signatory should carry only the PM role');
        System.assertEquals(
            new Set<String>{ ROLE_CREDENTIALING, ROLE_SIGNATORY },
            rolesOf(acrs.get('Sig').Roles),
            'A separate signatory should carry CS_Role__c plus Contract-Signature');
        System.assertEquals('sig@test.com', acrs.get('Sig').Contact.Email,
            'CS_Email__c mapping');
    }

    @IsTest
    static void testStep10FacilityManagerIsAlsoSignatory() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Step10 FM Yes Shell');
        Lead ld = getLead('fmyes');

        NS_DPAIntake_Form__c dpa = buildDpaWithContacts(ld.Id, false, 'Yes');
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Map<String, AccountContactRelation> acrs =
            officeStaffAcrs(convertedLead(ld.Id).ConvertedAccountId);
        System.assertEquals(true, acrs.containsKey('Facility'),
            'The FM path should produce a Contact from FM_First_Name__c. Found: '
            + acrs.keySet());
        System.assertEquals(
            new Set<String>{ ROLE_PRACTICE_MANAGER, ROLE_SIGNATORY },
            rolesOf(acrs.get('Facility').Roles),
            'buildManagerBlock maps the FM path to Practice Manager (not a '
            + 'Facility Manager role), plus Contract-Signature');
        System.assertEquals('fm@test.com', acrs.get('Facility').Contact.Email,
            'FM_Email__c mapping');
    }

    @IsTest
    static void testStep10SignatoryNoWithNoSignatoryData() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Step10 NoSigData Shell');
        Lead ld = getLead('nosigdata');

        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c     = String.valueOf(ld.Id),
            PM_First_Name__c      = 'Practice',
            PM_Last_Name__c       = 'Manager',
            Practice_Phone__c     = '4155554444',
            Practice_Email__c     = 'pm@test.com',
            Contract_Signatory__c = 'No'
        );
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Map<String, AccountContactRelation> acrs =
            officeStaffAcrs(convertedLead(ld.Id).ConvertedAccountId);
        System.assertEquals(1, acrs.size(),
            'Contract_Signatory__c = No with no CS_* data should log a WARNING '
            + 'and create only the PM Contact. Found: ' + acrs.keySet());
        System.assertEquals(new Set<String>{ ROLE_PRACTICE_MANAGER },
            rolesOf(acrs.get('Practice').Roles), 'PM role only');
    }

    @IsTest
    static void testStep10NoContactData() {
        Test.setMock(HttpCalloutMock.class, new PubSubMock());
        armShell('Step10 Empty Shell');
        Lead ld = getLead('nocontact');

        NS_DPAIntake_Form__c dpa = new NS_DPAIntake_Form__c(
            Lead_Record_ID__c = String.valueOf(ld.Id)
        );
        persistWithoutTriggering(dpa);

        Test.startTest();
        NS_DPAIntakeHelper.processLeadConversion(
            new Set<Id>{ ld.Id }, new List<NS_DPAIntake_Form__c>{ dpa }
        );
        Test.stopTest();

        Lead conv = convertedLead(ld.Id);
        System.assertEquals(true, conv.IsConverted, 'Lead should still convert');
        System.assertEquals(0, officeStaffAcrs(conv.ConvertedAccountId).size(),
            'A DPA with no contact-role data must skip Step 10 without creating '
            + 'Office Staff Contacts');
    }
}
