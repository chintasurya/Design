import { LightningElement, track } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import createRequest from '@salesforce/apex/AIChangeRequestController.createRequest';
import stepUnderstand from '@salesforce/apex/AIChangeRequestController.stepUnderstand';
import stepScope from '@salesforce/apex/AIChangeRequestController.stepScope';
import stepSearch from '@salesforce/apex/AIChangeRequestController.stepSearch';
import stepAssess from '@salesforce/apex/AIChangeRequestController.stepAssess';
import approveAnalysis from '@salesforce/apex/AIChangeRequestController.approveAnalysis';
import approveCode from '@salesforce/apex/AIChangeRequestController.approveCode';
import rejectRequest from '@salesforce/apex/AIChangeRequestController.rejectRequest';
import getView from '@salesforce/apex/AIChangeRequestController.getView';
import buildGraph from '@salesforce/apex/AIChangeRequestController.buildGraph';
import graphStatus from '@salesforce/apex/AIChangeRequestController.graphStatus';
import listProfiles from '@salesforce/apex/AIChangeRequestController.listProfiles';

const FINDING_COLUMNS = [
    { label: 'Type', fieldName: 'Node_Type__c', initialWidth: 120 },
    { label: 'Component', fieldName: 'Node_Name__c', wrapText: true },
    { label: 'How it connects', fieldName: 'Relationship_Path__c', wrapText: true },
    { label: 'Impact', fieldName: 'Impact__c', initialWidth: 95 },
    { label: 'Risk', fieldName: 'Risk_Tier__c', initialWidth: 80 },
    { label: 'Evidence in the org', fieldName: 'Provenance__c', wrapText: true }
];

const TEST_COLUMNS = [
    { label: 'Class', fieldName: 'Test_Class__c' },
    { label: 'Method', fieldName: 'Test_Method__c' },
    { label: 'Outcome', fieldName: 'Outcome__c', initialWidth: 100 },
    { label: 'Message', fieldName: 'Message__c', wrapText: true }
];

// Each entry is one real Apex round trip, not a timed animation.
const PIPELINE = [
    { key: 'understand', running: 'Reading the request', fn: stepUnderstand },
    { key: 'scope', running: 'Resolving the Network Services scope', fn: stepScope },
    { key: 'search', running: 'Searching live org metadata', fn: stepSearch },
    { key: 'assess', running: 'Assessing reuse against what exists', fn: stepAssess }
];

export default class AiChangeConsole extends LightningElement {
    @track view;
    @track steps = [];
    requestText = '';
    submittedText = '';
    requestType = 'Update Existing';
    model = 'Codex';
    busy = false;
    stepsExpanded = false;
    totalMs = 0;
    @track graph = { built: false, nodes: 0, edges: 0 };
    building = false;
    pollId;

    connectedCallback() {
        this.refreshGraph();
    }

    disconnectedCallback() {
        clearInterval(this.pollId);
    }

    @track profiles = [];
    allProfiles = [];
    profileFilter = '';
    showProfiles = false;

    get profileCountLabel() {
        return this.profiles.length === this.allProfiles.length
            ? `${this.allProfiles.length} profiles`
            : `${this.profiles.length} of ${this.allProfiles.length} profiles`;
    }

    handleProfileFilter(event) {
        this.profileFilter = event.target.value || '';
        this.applyProfileFilter();
    }

    applyProfileFilter() {
        const needle = this.profileFilter.trim().toLowerCase();
        this.profiles = needle
            ? this.allProfiles.filter((p) => p.name.toLowerCase().includes(needle))
            : this.allProfiles;
    }

    get scopeWarning() {
        if (!this.graph.scopeNote) {
            return null;
        }
        return this.graph.profileFound ? null : this.graph.scopeNote;
    }

    get scopeNote() {
        return this.graph.scopeNote;
    }

    get profileToggleLabel() {
        return this.showProfiles ? 'Hide profiles' : 'Show profiles in this org';
    }

    async toggleProfiles() {
        this.showProfiles = !this.showProfiles;
        if (this.showProfiles && this.profiles.length === 0) {
            try {
                const rows = await listProfiles();
                this.allProfiles = rows
                    .map((r) => ({
                        name: r.name,
                        detail: `${r.writable} objects writable`
                    }))
                    .sort((a, b) => a.name.localeCompare(b.name));
                this.applyProfileFilter();
            } catch (error) {
                this.toast('Could not list profiles', this.messageOf(error), 'error');
            }
        }
    }

    get graphLabel() {
        if (this.building) {
            return `Building the graph… ${this.graph.jobDone || 0} of ${this.graph.jobTotal || '?'} batches`;
        }
        if (this.graph.jobError) {
            return `Build failed: ${this.graph.jobError}`;
        }
        return this.graph.built
            ? `Graph: ${this.graph.nodes} nodes · ${this.graph.edges} edges · ` +
              `${this.graph.sizeKb} KB JSON`
            : 'Graph not exported yet';
    }

    get buildLabel() {
        return this.graph.built ? 'Re-export graph' : 'Export graph';
    }

    get graphClass() {
        if (this.graph.jobError) {
            return 'graphbar graphbar_failed';
        }
        return this.graph.built && !this.building
            ? 'graphbar graphbar_ready'
            : 'graphbar graphbar_empty';
    }

    get analyseDisabled() {
        return this.submitDisabled || !this.graph.built;
    }

    async refreshGraph() {
        try {
            this.graph = await graphStatus();
            const running =
                this.graph.jobStatus === 'Processing' ||
                this.graph.jobStatus === 'Queued' ||
                this.graph.jobStatus === 'Preparing';
            this.building = running;
            if (running && !this.pollId) {
                this.pollId = setInterval(() => this.refreshGraph(), 3000);
            } else if (!running && this.pollId) {
                clearInterval(this.pollId);
                this.pollId = undefined;
            }
        } catch (error) {
            this.toast('Could not read graph status', this.messageOf(error), 'error');
        }
    }

    async handleBuildGraph() {
        this.building = true;
        try {
            await buildGraph();
            this.toast('Exporting',
                'Walking the pod scope and writing graph-salesforce.json.',
                'success');
            await this.refreshGraph();
        } catch (error) {
            this.building = false;
            this.toast('Build failed', this.messageOf(error), 'error');
        }
    }

    findingColumns = FINDING_COLUMNS;
    testColumns = TEST_COLUMNS;

    get typeOptions() {
        return [
            { label: 'Change something that exists', value: 'Update Existing' },
            { label: 'Add something new', value: 'New Enhancement' }
        ];
    }

    get models() {
        return ['Codex', 'Claude', 'Gemini'].map((name) => ({
            name,
            variant: this.model === name ? 'brand' : 'neutral'
        }));
    }

    get hasRequest() {
        return !!this.view;
    }

    // Always on screen. Swapping the composer out for results was the thing
    // that made this feel like a second page.
    get composerLabel() {
        return this.steps.length > 0 ? 'Refine and run again' : 'What do you need changed?';
    }

    get submitLabel() {
        return this.steps.length > 0 ? 'Re-analyse' : 'Analyse';
    }

    get hasResult() {
        return this.steps.length > 0;
    }

    get showSteps() {
        return this.steps.length > 0;
    }

    get stepsDone() {
        return (
            this.steps.length > 0 &&
            this.steps.every((s) => s.state === 'done' || s.state === 'failed')
        );
    }

    get showStepList() {
        return this.steps.length > 0 && (!this.stepsDone || this.stepsExpanded);
    }

    get showStepSummary() {
        return this.stepsDone && !this.stepsExpanded;
    }

    get stepsFailed() {
        return this.steps.some((s) => s.state === 'failed');
    }

    get stepsSummary() {
        const done = this.steps.filter((s) => s.state === 'done').length;
        const secs = (this.totalMs / 1000).toFixed(1);
        return this.stepsFailed
            ? `Analysis stopped after ${done} of ${this.steps.length} steps`
            : `Analysed in ${secs}s · ${done} steps`;
    }

    get stepsSummaryIcon() {
        return this.stepsFailed ? 'utility:error' : 'utility:check';
    }

    get stepsSummaryClass() {
        return this.stepsFailed
            ? 'summaryline summaryline_failed'
            : 'summaryline summaryline_done';
    }

    get toggleLabel() {
        return this.stepsExpanded ? 'Hide steps' : 'Show steps';
    }

    toggleSteps() {
        this.stepsExpanded = !this.stepsExpanded;
    }

    get status() {
        return this.view ? this.view.request.Status__c : 'Draft';
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

    get verdict() {
        return this.view ? this.view.verdict : null;
    }

    get hasFindings() {
        return this.findings.length > 0;
    }

    get showArtifacts() {
        return this.artifacts.length > 0;
    }

    get showTests() {
        return this.testResults.length > 0;
    }

    get snapshotLine() {
        if (!this.view) {
            return '';
        }
        return `${this.view.request.Snapshot_Id__c} · ${this.findings.length} components`;
    }

    get verdictClass() {
        const o = this.verdict && this.verdict.outcome;
        const base = 'slds-box slds-var-m-bottom_small verdict ';
        if (o === 'Already Exists') return base + 'verdict_warn';
        if (o === 'Safe to Create') return base + 'verdict_ok';
        if (o === 'Needs Clarification') return base + 'verdict_muted';
        return base + 'verdict_info';
    }

    get verdictIcon() {
        const o = this.verdict && this.verdict.outcome;
        if (o === 'Already Exists') return 'utility:warning';
        if (o === 'Safe to Create') return 'utility:success';
        if (o === 'Needs Clarification') return 'utility:help';
        return 'utility:info';
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

    get gateLabel() {
        if (this.verdict && this.verdict.blocksCreation) {
            return 'This would duplicate something that already exists. Approve only if you intend to override that.';
        }
        return this.atAnalysisGate
            ? 'Approve to raise a Jira ticket and build the prompt from these components only'
            : 'Approve to deploy the generated change to this sandbox';
    }

    get submitDisabled() {
        return this.busy || !this.requestText || this.requestText.trim().length === 0;
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

    handleReset() {
        this.view = null;
        this.steps = [];
        this.requestText = '';
        this.submittedText = '';
        this.stepsExpanded = false;
        this.totalMs = 0;
    }

    /**
     * Walk the pipeline one call at a time, repainting between each so the
     * user sees each step land as the work behind it actually finishes.
     */
    async handleSubmit() {
        this.busy = true;
        this.view = null;
        this.submittedText = this.requestText.trim();
        this.stepsExpanded = false;
        this.totalMs = 0;
        const started = Date.now();
        this.steps = PIPELINE.map((s) => ({
            key: s.key,
            label: s.running,
            detail: '',
            state: 'waiting',
            icon: 'utility:routing_offline',
            css: 'step step_waiting'
        }));

        try {
            const requestId = await createRequest({
                requestText: this.requestText,
                requestType: this.requestType,
                model: this.model
            });

            for (let i = 0; i < PIPELINE.length; i++) {
                this.mark(i, 'running');
                const result = await PIPELINE[i].fn({ requestId });
                if (PIPELINE[i].key === 'assess') {
                    this.view = result;
                    this.mark(i, 'done', this.verdict ? this.verdict.headline : '');
                } else {
                    this.mark(i, 'done', result.detail, result.elapsedMs);
                }
            }
        } catch (error) {
            const idx = this.steps.findIndex((s) => s.state === 'running');
            if (idx >= 0) {
                this.mark(idx, 'failed', this.messageOf(error));
            }
            this.toast('Analysis stopped', this.messageOf(error), 'error');
        } finally {
            this.totalMs = Date.now() - started;
            this.busy = false;
        }
    }

    mark(index, state, detail, elapsedMs) {
        const icons = {
            waiting: 'utility:routing_offline',
            running: 'utility:sync',
            done: 'utility:check',
            failed: 'utility:error'
        };
        const next = [...this.steps];
        next[index] = {
            ...next[index],
            state,
            detail: detail === undefined ? next[index].detail : detail,
            elapsed: elapsedMs ? `${elapsedMs} ms` : '',
            icon: icons[state],
            css: `step step_${state}`
        };
        this.steps = next;
    }

    async handleApprove() {
        await this.run(this.atAnalysisGate ? approveAnalysis : approveCode, 'Approved');
    }

    async handleReject() {
        await this.run(rejectRequest, 'Rejected', { reason: 'Rejected by reviewer' });
    }

    async handleRefresh() {
        await this.run(getView, null);
    }

    async run(action, title, extra = {}) {
        if (!this.view) {
            return;
        }
        this.busy = true;
        try {
            this.view = await action({ requestId: this.view.request.Id, ...extra });
            if (title) {
                this.toast(title, `Status is now ${this.status}`, 'success');
            }
        } catch (error) {
            this.toast('Something went wrong', this.messageOf(error), 'error');
        } finally {
            this.busy = false;
        }
    }

    messageOf(error) {
        return (
            error?.body?.message ||
            error?.message ||
            'Unexpected error. Check the debug logs.'
        );
    }

    toast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }
}
