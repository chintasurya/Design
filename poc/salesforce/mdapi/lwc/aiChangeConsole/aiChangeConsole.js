import { LightningElement, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import createRequest from '@salesforce/apex/AIChangeRequestController.createRequest';
import runAnalysis from '@salesforce/apex/AIChangeRequestController.runAnalysis';
import approveAnalysis from '@salesforce/apex/AIChangeRequestController.approveAnalysis';
import approveCode from '@salesforce/apex/AIChangeRequestController.approveCode';
import rejectRequest from '@salesforce/apex/AIChangeRequestController.rejectRequest';
import getView from '@salesforce/apex/AIChangeRequestController.getView';

const FINDING_COLUMNS = [
    { label: 'Source', fieldName: 'Source_System__c', initialWidth: 110 },
    { label: 'Type', fieldName: 'Node_Type__c', initialWidth: 130 },
    { label: 'Component', fieldName: 'Node_Name__c', wrapText: true },
    { label: 'How it connects', fieldName: 'Relationship_Path__c', wrapText: true },
    { label: 'Impact', fieldName: 'Impact__c', initialWidth: 100 },
    { label: 'Risk', fieldName: 'Risk_Tier__c', initialWidth: 90 },
    { label: 'Evidence', fieldName: 'Provenance__c', wrapText: true }
];

const TEST_COLUMNS = [
    { label: 'Class', fieldName: 'Test_Class__c' },
    { label: 'Method', fieldName: 'Test_Method__c' },
    { label: 'Outcome', fieldName: 'Outcome__c', initialWidth: 100 },
    { label: 'Message', fieldName: 'Message__c', wrapText: true }
];

export default class AiChangeConsole extends LightningElement {
    @track view;
    requestText = '';
    requestType = 'Update Existing';
    model = 'Codex';
    loading = false;

    findingColumns = FINDING_COLUMNS;
    testColumns = TEST_COLUMNS;

    get typeOptions() {
        return [
            { label: 'Update an existing feature', value: 'Update Existing' },
            { label: 'New enhancement', value: 'New Enhancement' }
        ];
    }

    get models() {
        return ['Codex', 'Claude', 'Gemini'].map((name) => ({
            name,
            variant: this.model === name ? 'brand' : 'neutral'
        }));
    }

    get status() {
        return this.view ? this.view.request.Status__c : 'Draft';
    }

    get hasRequest() {
        return !!this.view;
    }

    get requestName() {
        return this.view ? this.view.request.Name : '';
    }

    get findings() {
        return this.view ? this.view.findings : [];
    }

    get testResults() {
        return this.view ? this.view.testResults : [];
    }

    get artifacts() {
        return this.view ? this.view.artifacts : [];
    }

    get findingCount() {
        return this.findings.length;
    }

    get analysisSummary() {
        return this.view ? this.view.request.Analysis_Summary__c : '';
    }

    get errorMessage() {
        return this.view ? this.view.request.Error_Message__c : '';
    }

    get snapshotId() {
        return this.view ? this.view.request.Snapshot_Id__c : '';
    }

    get submitDisabled() {
        return this.loading || !this.requestText || this.requestText.trim().length === 0;
    }

    get showAnalysis() {
        return this.hasRequest && this.findingCount > 0;
    }

    get atAnalysisGate() {
        return this.status === 'Awaiting Analysis Approval';
    }

    get atCodeGate() {
        return this.status === 'Awaiting Code Approval';
    }

    get atAnyGate() {
        return this.atAnalysisGate || this.atCodeGate;
    }

    get showArtifacts() {
        return this.artifacts.length > 0;
    }

    get showTests() {
        return this.testResults.length > 0;
    }

    get gateLabel() {
        return this.atAnalysisGate
            ? 'Approve these findings to open a Jira ticket and build the prompt'
            : 'Approve the generated change to deploy it to this sandbox';
    }

    get statusVariant() {
        if (this.status === 'Complete') {
            return 'success';
        }
        if (this.status === 'Failed' || this.status === 'Rejected') {
            return 'error';
        }
        return this.atAnyGate ? 'warning' : 'inverse';
    }

    handleText(event) {
        this.requestText = event.target.value;
    }

    handleType(event) {
        this.requestType = event.detail.value;
    }

    handleModel(event) {
        this.model = event.target.dataset.model;
    }

    async handleSubmit() {
        this.loading = true;
        try {
            const requestId = await createRequest({
                requestText: this.requestText,
                requestType: this.requestType,
                model: this.model
            });
            this.view = await runAnalysis({ requestId });
            this.toast('Graph searched', `${this.findingCount} connected components found`, 'success');
        } catch (error) {
            this.fail(error);
        } finally {
            this.loading = false;
        }
    }

    async handleApprove() {
        const action = this.atAnalysisGate ? approveAnalysis : approveCode;
        await this.run(action, 'Approved');
    }

    async handleReject() {
        await this.run(rejectRequest, 'Rejected', { reason: 'Rejected by reviewer' });
    }

    async handleRefresh() {
        await this.run(getView, null);
    }

    handleReset() {
        this.view = null;
        this.requestText = '';
    }

    async run(action, successTitle, extra = {}) {
        if (!this.view) {
            return;
        }
        this.loading = true;
        try {
            this.view = await action({ requestId: this.view.request.Id, ...extra });
            if (successTitle) {
                this.toast(successTitle, `Status is now ${this.status}`, 'success');
            }
        } catch (error) {
            this.fail(error);
        } finally {
            this.loading = false;
        }
    }

    fail(error) {
        const message =
            error?.body?.message || error?.message || 'Unexpected error. Check debug logs.';
        this.toast('Something went wrong', message, 'error');
    }

    toast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }
}
