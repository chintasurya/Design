import { LightningElement } from 'lwc';
import status from '@salesforce/apex/AgentConsoleController.status';
import connectCodex from '@salesforce/apex/AgentConsoleController.connectCodex';
import codexLoginStatus from '@salesforce/apex/AgentConsoleController.codexLoginStatus';
import codexLogout from '@salesforce/apex/AgentConsoleController.codexLogout';
import codexCompleteLogin from '@salesforce/apex/AgentConsoleController.codexCompleteLogin';
import listTickets from '@salesforce/apex/AgentConsoleController.listTickets';
import askRequirementAgent from '@salesforce/apex/AgentConsoleController.askRequirementAgent';
import startDevelopment from '@salesforce/apex/AgentConsoleController.startDevelopment';
import getRun from '@salesforce/apex/AgentConsoleController.getRun';
import approveDeployment from '@salesforce/apex/AgentConsoleController.approveDeployment';
import rejectDeployment from '@salesforce/apex/AgentConsoleController.rejectDeployment';
import rebuildGraph from '@salesforce/apex/AgentConsoleController.rebuildGraph';

const POLL_MS = 2500;
const STOP = new Set(['succeeded', 'failed', 'rejected', 'waiting_approval']);
const STEP_ICON = {
    done: 'utility:success',
    running: 'utility:clock',
    waiting: 'utility:pause',
    error: 'utility:error'
};
const STATUS_LABEL = {
    queued: 'Queued',
    running: 'Working',
    waiting_approval: 'Waiting for your approval',
    succeeded: 'Done',
    failed: 'Failed',
    rejected: 'Rejected'
};
const SUGGESTIONS = [
    'List my open tickets',
    'Which tickets are ready for development?',
    'What does the org already have on Account?'
];

function errorText(e) {
    if (!e) return 'Unknown error';
    if (e.body && e.body.message) return e.body.message;
    return e.message || String(e);
}

function keyed(list) {
    return (list || []).map((text, i) => ({ key: String(i), text }));
}

function stepItems(run) {
    return ((run && run.steps) || []).map((s, i) => ({
        key: String(i),
        name: s.name,
        detail: s.detail,
        iconName: STEP_ICON[s.status] || STEP_ICON.done,
        iconVariant: s.status === 'error' ? 'error' : s.status === 'done' ? 'success' : 'warning',
        cssClass: 'step step_' + (s.status || 'done')
    }));
}

export default class AgentConsole extends LightningElement {
    // connection: every time the console opens it starts here, by design
    connected = false;
    connecting = false;
    needsKey = false;
    apiKey = '';
    connectMessage = '';
    codex;
    device; // pending Codex sign-in: browser (authUrl) or device (verificationUrl, userCode), expiresAt
    redirectUrl = '';
    finishing = false;
    gateway;
    gatewayError;

    // requirement agent
    messages = [];
    draft = '';
    conversationId;
    chatRun;
    sending = false;
    tickets = [];
    ticketsLoading = false;
    spec;
    developAnyway = false;

    // developer agent
    devRun;
    devBusy = false;
    openFile;

    // knowledge graph
    graphRun;

    timers = {};
    seq = 0;

    connectedCallback() {
        this.loadStatus();
    }

    disconnectedCallback() {
        Object.values(this.timers).forEach((t) => clearTimeout(t));
    }

    // ---------------------------------------------------------------- status
    async loadStatus() {
        try {
            this.gateway = JSON.parse(await status());
            this.gatewayError = undefined;
        } catch (e) {
            this.gatewayError = errorText(e);
        }
    }

    get statusRows() {
        const g = this.gateway || {};
        const jira = g.jira || {};
        const sf = g.salesforce || {};
        const graph = g.graph || {};
        const row = (key, label, ok, value) => ({
            key,
            label,
            value,
            iconName: ok ? 'utility:success' : 'utility:warning',
            iconVariant: ok ? 'success' : 'warning'
        });
        return [
            row('jira', 'Jira', jira.configured, jira.configured ? `${jira.site} · project ${jira.project}` : 'Not configured on the gateway'),
            row('sf', 'Salesforce', sf.configured, sf.configured ? sf.loginUrl : 'Not configured on the gateway'),
            row('graph', 'Knowledge graph', graph.nodes > 0, this.graphLabel)
        ];
    }

    get graphLabel() {
        const graph = (this.gateway && this.gateway.graph) || {};
        if (graph.error) return `Unavailable: ${graph.error}`;
        if (!graph.nodes) return 'Not built yet. Build it once before asking about tickets.';
        const built = graph.built_at ? ` · built ${new Date(graph.built_at).toLocaleString()}` : '';
        return `${graph.nodes} nodes · ${graph.edges} edges${built}`;
    }

    get jiraProject() {
        return (this.gateway && this.gateway.jira && this.gateway.jira.project) || 'Jira';
    }

    // --------------------------------------------------------------- connect
    handleApiKey(event) {
        this.apiKey = event.target.value;
    }

    async handleConnect() {
        this.connecting = true;
        this.connectMessage = '';
        try {
            const r = JSON.parse(await connectCodex({ apiKey: this.apiKey || null }));
            this.apiKey = '';
            this.applyConnect(r);
        } catch (e) {
            this.connectMessage = errorText(e);
        } finally {
            this.connecting = false;
        }
    }

    // One shape for both modes: the developer's own Codex sign-in (chatgpt) or a gateway key (apikey).
    applyConnect(r) {
        this.connectMessage = r.message || '';
        this.needsKey = r.mode === 'apikey' && !r.connected && !!r.needsKey;
        this.device = r.mode === 'chatgpt' && r.pending ? r : undefined;
        clearTimeout(this.timers.login);
        if (this.device && this.device.flow !== 'browser') {
            // poll until the developer approves the code in their browser
            // eslint-disable-next-line @lwc/lwc/no-async-operation
            this.timers.login = setTimeout(() => this.pollLogin(), 3000);
        }
        if (r.connected) {
            this.codex = r;
            this.connected = true;
            this.loadStatus();
            this.loadTickets();
            this.pushAgent(
                `${this.codexLabel}. Ask me about any ${this.jiraProject} ticket, ` +
                    'or pick one on the left and I will turn it into a development-ready spec.'
            );
        }
    }

    async pollLogin() {
        try {
            this.applyConnect(JSON.parse(await codexLoginStatus()));
        } catch (e) {
            this.device = undefined;
            this.connectMessage = errorText(e);
        }
    }

    get isBrowserFlow() {
        return !!this.device && this.device.flow === 'browser';
    }

    get isDeviceFlow() {
        return !!this.device && this.device.flow !== 'browser';
    }

    get finishDisabled() {
        return this.finishing || !this.redirectUrl.trim();
    }

    get finishLabel() {
        return this.finishing ? 'Connecting…' : 'Finish connecting';
    }

    handleRedirectUrl(event) {
        this.redirectUrl = event.target.value;
    }

    async handleFinishLogin() {
        this.finishing = true;
        this.connectMessage = '';
        try {
            const r = JSON.parse(await codexCompleteLogin({ redirectUrl: this.redirectUrl }));
            this.redirectUrl = '';
            this.applyConnect(r);
        } catch (e) {
            this.connectMessage = errorText(e);
        } finally {
            this.finishing = false;
        }
    }

    async handleSignOut() {
        try {
            await codexLogout();
        } catch (e) {
            this.pushAgent(errorText(e), true);
            return;
        }
        this.connected = false;
        this.codex = undefined;
        this.device = undefined;
        this.connectMessage = 'Signed out of Codex.';
    }

    get isChatgptMode() {
        return !!this.codex && this.codex.mode === 'chatgpt';
    }

    get deviceExpires() {
        return this.device && this.device.expiresAt
            ? new Date(this.device.expiresAt * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : '';
    }

    get notConnected() {
        return !this.connected;
    }

    get connectLabel() {
        return this.connecting ? 'Connecting…' : 'Connect to Codex';
    }

    get connectDisabled() {
        return this.connecting || !!this.device || (this.needsKey && !this.apiKey);
    }

    get codexLabel() {
        const c = this.codex;
        if (!c) return 'Codex';
        if (c.mode === 'chatgpt') {
            const a = c.account || {};
            const who = [a.email, a.plan ? a.plan.charAt(0).toUpperCase() + a.plan.slice(1) : ''].filter(Boolean);
            return who.length ? `Connected to your Codex · ${who.join(' · ')}` : 'Connected to your Codex';
        }
        return `Connected to Codex · ${c.model}`;
    }

    // ---------------------------------------------------------------- tickets
    async loadTickets() {
        this.ticketsLoading = true;
        try {
            const r = JSON.parse(await listTickets({ onlyOpen: true }));
            this.tickets = (r.tickets || []).map((t) => ({ ...t, label: `${t.key} · ${t.summary}` }));
        } catch (e) {
            this.pushAgent(`Could not list tickets: ${errorText(e)}`, true);
        } finally {
            this.ticketsLoading = false;
        }
    }

    get hasTickets() {
        return this.tickets.length > 0;
    }

    handleAnalyzeTicket(event) {
        this.send(`Analyze ${event.currentTarget.dataset.key} and prepare it for development.`);
    }

    // ------------------------------------------------------------------- chat
    get messageItems() {
        return this.messages.map((m) => ({
            ...m,
            cssClass: `msg msg_${m.role}${m.isError ? ' msg_error' : ''}`
        }));
    }

    get suggestions() {
        return SUGGESTIONS.map((text) => ({ key: text, text }));
    }

    get chatBusy() {
        return this.sending || !!this.chatRun;
    }

    get sendDisabled() {
        return this.chatBusy || !this.draft.trim();
    }

    get chatSteps() {
        return stepItems(this.chatRun);
    }

    pushUser(text) {
        this.seq += 1;
        this.messages = [...this.messages, { id: `m${this.seq}`, role: 'user', author: 'You', text }];
    }

    pushAgent(text, isError) {
        this.seq += 1;
        this.messages = [
            ...this.messages,
            { id: `m${this.seq}`, role: 'agent', author: 'Requirement agent', text, isError: !!isError }
        ];
    }

    handleDraft(event) {
        this.draft = event.target.value;
    }

    handleDraftKey(event) {
        if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
            this.handleSend();
        }
    }

    handleSend() {
        this.send(this.draft);
    }

    handleSuggestion(event) {
        this.send(event.currentTarget.dataset.text);
    }

    handleNewConversation() {
        this.conversationId = undefined;
        this.messages = [];
        this.spec = undefined;
        this.devRun = undefined;
        this.pushAgent('New conversation. Which ticket should we look at?');
    }

    async send(text) {
        const message = (text || '').trim();
        if (!message || this.chatBusy) return;
        this.pushUser(message);
        this.draft = '';
        this.sending = true;
        try {
            const r = JSON.parse(await askRequirementAgent({ message, conversationId: this.conversationId || null }));
            this.conversationId = r.conversationId;
            this.chatRun = { status: 'queued', steps: [] };
            this.poll(
                'chat',
                r.runId,
                (run) => {
                    this.chatRun = run;
                },
                (run) => {
                    this.chatRun = undefined;
                    if (run.status === 'succeeded' && run.result) {
                        this.pushAgent(run.result.reply || '(no reply)');
                        if (run.result.spec) {
                            this.spec = run.result.spec;
                            this.developAnyway = false;
                            this.devRun = undefined;
                            if (run.result.build) this.buildFromChat();
                        }
                    } else {
                        this.pushAgent(`The Requirement agent stopped: ${run.error || run.status}`, true);
                    }
                }
            );
        } catch (e) {
            this.pushAgent(errorText(e), true);
        } finally {
            this.sending = false;
        }
    }

    // "build KAN-16" in the chat: develop straight away when the spec is ready.
    // Deployment still waits for the Approve button.
    buildFromChat() {
        const key = this.spec.ticket_key;
        if (!this.specReady) {
            const open = (this.spec.open_questions || []).slice(0, 3).map((q) => `- ${q}`).join('\n');
            this.pushAgent(`${key} is not ready for development yet, so I did not start building.` +
                (open ? `\nOpen questions:\n${open}` : '') + '\nAnswer them, or tick "Develop anyway" and press Develop.');
            return;
        }
        this.pushAgent(`Building ${key}: the Developer agent has started. You approve before anything is deployed.`);
        this.handleDevelop();
    }

    // ------------------------------------------------------------------- spec
    get hasSpec() {
        return !!this.spec;
    }

    get specTitle() {
        return this.spec ? `${this.spec.ticket_key} · ${this.spec.title}` : '';
    }

    get specUrl() {
        return this.spec && (this.spec.ticket_url || (this.spec.ticket && this.spec.ticket.url));
    }

    get specComponents() {
        return ((this.spec && this.spec.components) || []).map((c, i) => ({
            ...c,
            key: String(i),
            actionLabel: c.action === 'create' ? 'Create' : 'Modify',
            existsLabel: c.exists_in_org ? 'Exists in org' : 'New',
            existsClass: c.exists_in_org ? 'tag tag_exists' : 'tag tag_new'
        }));
    }

    get specCriteria() {
        return keyed(this.spec && this.spec.acceptance_criteria);
    }

    get specReuse() {
        return keyed(this.spec && this.spec.reuse);
    }

    get specImpact() {
        return keyed(this.spec && this.spec.impact);
    }

    get specTests() {
        return keyed(this.spec && this.spec.test_plan);
    }

    get specQuestions() {
        return keyed(this.spec && this.spec.open_questions);
    }

    get hasReuse() {
        return this.specReuse.length > 0;
    }

    get hasImpact() {
        return this.specImpact.length > 0;
    }

    get hasQuestions() {
        return this.specQuestions.length > 0;
    }

    get specReady() {
        return !!(this.spec && this.spec.ready_for_development);
    }

    get specNotReady() {
        return !this.specReady;
    }

    get readyLabel() {
        return this.specReady ? 'Ready for development' : 'Not ready: open questions';
    }

    get readyClass() {
        return this.specReady ? 'tag tag_exists' : 'tag tag_warn';
    }

    get approach() {
        return (this.spec && this.spec.approach) || null;
    }

    get approachLabel() {
        const a = this.approach;
        return a ? `Build with: ${a.build_with}` : '';
    }

    get approachClass() {
        const a = this.approach;
        return a && ['Flow', 'Configuration'].includes(a.build_with) ? 'tag tag_exists' : 'tag tag_warn';
    }

    get hasWhyNotFlow() {
        return !!(this.approach && this.approach.why_not_flow && this.approach.why_not_flow.trim());
    }

    get hasExistingAutomation() {
        return !!(this.approach && this.approach.existing_automation && this.approach.existing_automation.trim());
    }

    // ------------------------------------------------------------ guardrails
    get guardrails() {
        return this.devResult.guardrails || null;
    }

    get guardrailSummary() {
        const g = this.guardrails;
        if (!g) return '';
        const passed = (g.passed || []).length;
        const checked = (g.checked || []).length;
        const warn = (g.warnings || []).length;
        return `${g.pack} (v${g.version}): ${passed} of ${checked} checked rules passed` +
            (warn ? ` · ${warn} warning${warn === 1 ? '' : 's'}` : ' · no warnings');
    }

    get guardrailWarnings() {
        return ((this.guardrails && this.guardrails.warnings) || []).map((w, i) => ({
            key: String(i),
            text: `[${w.rule}] ${w.title}: ${w.message} (${(w.file || '').replace('force-app/main/default/', '')})`
        }));
    }

    get hasGuardrailWarnings() {
        return this.guardrailWarnings.length > 0;
    }

    get riskLabel() {
        return this.spec ? `Risk: ${this.spec.risk}` : '';
    }

    get developDisabled() {
        return this.devBusy || this.devActive || (!this.specReady && !this.developAnyway);
    }

    handleDevelopAnyway(event) {
        this.developAnyway = event.target.checked;
    }

    // -------------------------------------------------------------- developer
    get devActive() {
        return !!this.devRun && !STOP.has(this.devRun.status);
    }

    get devStatusLabel() {
        return this.devRun ? STATUS_LABEL[this.devRun.status] || this.devRun.status : '';
    }

    get devStatusClass() {
        const s = this.devRun && this.devRun.status;
        if (s === 'succeeded') return 'tag tag_exists';
        if (s === 'failed' || s === 'rejected') return 'tag tag_error';
        return 'tag tag_warn';
    }

    get devSteps() {
        return stepItems(this.devRun);
    }

    get devResult() {
        return (this.devRun && this.devRun.result) || {};
    }

    get devFiles() {
        return (this.devResult.files || []).map((f) => ({
            ...f,
            key: f.path,
            name: f.path.replace('force-app/main/default/', ''),
            isOpen: f.path === this.openFile
        }));
    }

    get hasDevFiles() {
        return this.devFiles.length > 0;
    }

    get devWaiting() {
        return !!this.devRun && this.devRun.status === 'waiting_approval';
    }

    get devDeployed() {
        return !!this.devRun && this.devRun.status === 'succeeded';
    }

    get devFailed() {
        return !!this.devRun && this.devRun.status === 'failed';
    }

    get validationText() {
        const v = this.devResult.validation;
        if (!v) return '';
        const tests = this.devResult.tests && this.devResult.tests.length ? this.devResult.tests.join(', ') : 'none';
        return `Check-only deploy passed · tests run: ${v.tests_run || 0} (${tests})`;
    }

    get deploymentText() {
        const d = this.devResult.deployment;
        return d ? `Deploy ${d.id} · ${d.components_deployed || 0} components` : '';
    }

    get deployErrors() {
        const d = this.devResult.deployment;
        return keyed(d && d.errors);
    }

    handleToggleFile(event) {
        const path = event.currentTarget.dataset.path;
        this.openFile = this.openFile === path ? undefined : path;
    }

    async handleDevelop() {
        if (!this.spec) return;
        this.devBusy = true;
        try {
            const r = JSON.parse(
                await startDevelopment({
                    ticketKey: this.spec.ticket_key,
                    specJson: JSON.stringify(this.spec),
                    developAnyway: this.developAnyway
                })
            );
            this.devRun = { id: r.runId, status: 'queued', steps: [] };
            this.pollDev(r.runId);
        } catch (e) {
            this.devRun = { status: 'failed', error: errorText(e), steps: [] };
        } finally {
            this.devBusy = false;
        }
    }

    pollDev(runId) {
        this.poll(
            'dev',
            runId,
            (run) => {
                this.devRun = run;
            },
            (run) => {
                this.devRun = run;
                if (run.status === 'succeeded') this.loadStatus();
            }
        );
    }

    async handleDeploy() {
        this.devBusy = true;
        try {
            await approveDeployment({ runId: this.devRun.id });
            this.devRun = { ...this.devRun, status: 'queued' };
            this.pollDev(this.devRun.id);
        } catch (e) {
            this.devRun = { ...this.devRun, error: errorText(e) };
        } finally {
            this.devBusy = false;
        }
    }

    async handleReject() {
        this.devBusy = true;
        try {
            await rejectDeployment({ runId: this.devRun.id });
            this.devRun = JSON.parse(await getRun({ runId: this.devRun.id }));
        } catch (e) {
            this.devRun = { ...this.devRun, error: errorText(e) };
        } finally {
            this.devBusy = false;
        }
    }

    // ------------------------------------------------------------------ graph
    get graphBusy() {
        return !!this.graphRun && !STOP.has(this.graphRun.status);
    }

    get graphSteps() {
        return stepItems(this.graphRun);
    }

    get rebuildLabel() {
        return this.graphBusy ? 'Building…' : 'Rebuild knowledge graph';
    }

    async handleRebuild() {
        try {
            const r = JSON.parse(await rebuildGraph());
            this.graphRun = { status: 'queued', steps: [] };
            this.poll(
                'graph',
                r.runId,
                (run) => {
                    this.graphRun = run;
                },
                (run) => {
                    this.graphRun = run;
                    this.loadStatus();
                }
            );
        } catch (e) {
            this.graphRun = { status: 'failed', steps: [], error: errorText(e) };
        }
    }

    // ------------------------------------------------------------------- poll
    poll(slot, runId, onUpdate, onDone) {
        clearTimeout(this.timers[slot]);
        const tick = async () => {
            let run;
            try {
                run = JSON.parse(await getRun({ runId }));
            } catch (e) {
                onDone({ id: runId, status: 'failed', error: errorText(e), steps: [] });
                return;
            }
            onUpdate(run);
            if (STOP.has(run.status)) {
                onDone(run);
                return;
            }
            // eslint-disable-next-line @lwc/lwc/no-async-operation
            this.timers[slot] = setTimeout(tick, POLL_MS);
        };
        // eslint-disable-next-line @lwc/lwc/no-async-operation
        this.timers[slot] = setTimeout(tick, 800);
    }
}
