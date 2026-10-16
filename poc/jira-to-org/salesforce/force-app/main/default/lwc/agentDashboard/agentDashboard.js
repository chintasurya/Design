import { LightningElement } from 'lwc';
import usageSummary from '@salesforce/apex/AgentConsoleController.usageSummary';

// Categorical slots 1 and 2 of the validated palette, in fixed order.
const SERIES = [
    { key: 'requirement', label: 'Requirement agent', color: '#2a78d6' },
    { key: 'developer', label: 'Developer agent', color: '#eb6834' }
];
const W = 760;
const H = 280;
const PAD = { left: 56, right: 16, top: 20, bottom: 34 };
const GAP = 2; // surface gap between stacked segments

function errorText(e) {
    return (e && e.body && e.body.message) || (e && e.message) || String(e);
}

function fmt(n) {
    return Number(n || 0).toLocaleString();
}

function short(n) {
    const v = Number(n || 0);
    if (v >= 1e6) return `${(v / 1e6).toFixed(v >= 1e7 ? 0 : 1)}M`;
    if (v >= 1e3) return `${(v / 1e3).toFixed(v >= 1e4 ? 0 : 1)}k`;
    return String(v);
}

function niceMax(v) {
    if (v <= 0) return 1000;
    const p = 10 ** Math.floor(Math.log10(v));
    const m = [1, 2, 2.5, 5, 10].find((s) => s * p >= v);
    return m * p;
}

// A bar segment with only its data end rounded.
function topRounded(x, y, w, h, r) {
    if (h <= 0) return '';
    const rr = Math.min(r, h, w / 2);
    return `M ${x} ${y + h} L ${x} ${y + rr} Q ${x} ${y} ${x + rr} ${y} L ${x + w - rr} ${y} ` +
        `Q ${x + w} ${y} ${x + w} ${y + rr} L ${x + w} ${y + h} Z`;
}

function square(x, y, w, h) {
    return h > 0 ? `M ${x} ${y} H ${x + w} V ${y + h} H ${x} Z` : '';
}

export default class AgentDashboard extends LightningElement {
    viewBox = `0 0 ${W} ${H}`;
    days = '14';
    data;
    loading = false;
    error;
    hoverIndex = -1;

    dayOptions = [
        { label: 'Last 7 days', value: '7' },
        { label: 'Last 14 days', value: '14' },
        { label: 'Last 30 days', value: '30' },
        { label: 'Last 90 days', value: '90' }
    ];

    connectedCallback() {
        this.load();
    }

    async load() {
        this.loading = true;
        this.error = undefined;
        try {
            this.data = JSON.parse(await usageSummary({ days: Number(this.days) }));
        } catch (e) {
            this.error = errorText(e);
        } finally {
            this.loading = false;
        }
    }

    handleDays(event) {
        this.days = event.detail.value;
        this.load();
    }

    handleRefresh() {
        this.load();
    }

    // ----------------------------------------------------------------- tiles
    get agents() {
        return (this.data && this.data.agents) || {};
    }

    get hasData() {
        return !!this.data && this.data.total_tokens > 0;
    }

    get emptyText() {
        return this.data
            ? `No model calls in the last ${this.data.days} days. Usage appears here after the first Requirement or Developer agent run.`
            : '';
    }

    get tiles() {
        const a = this.agents;
        const req = a.requirement || {};
        const dev = a.developer || {};
        const ok = (dev.outcomes && dev.outcomes.succeeded) || 0;
        return [
            { key: 'total', label: 'Total tokens', value: fmt(this.data && this.data.total_tokens),
                sub: `${fmt((req.runs || 0) + (dev.runs || 0))} agent runs` },
            { key: 'req', label: 'Requirement agent', value: fmt(req.total_tokens), swatch: `background:${SERIES[0].color}`,
                sub: `${fmt(req.runs)} runs · ${fmt(req.calls)} model calls · avg ${fmt(req.avg_per_run)} per run` },
            { key: 'dev', label: 'Developer agent', value: fmt(dev.total_tokens), swatch: `background:${SERIES[1].color}`,
                sub: `${fmt(dev.runs)} runs · ${fmt(dev.calls)} Codex attempts · avg ${fmt(dev.avg_per_run)} per run` },
            { key: 'mix', label: 'Input / output', value: `${short((req.input_tokens || 0) + (dev.input_tokens || 0))} / ${short((req.output_tokens || 0) + (dev.output_tokens || 0))}`,
                sub: `${short((req.cached_input_tokens || 0) + (dev.cached_input_tokens || 0))} input tokens served from cache · ${fmt(ok)} deployed` }
        ];
    }

    get legend() {
        const a = this.agents;
        return SERIES.map((s) => ({
            key: s.key,
            label: `${s.label} · ${fmt((a[s.key] || {}).total_tokens)}`,
            style: `background:${s.color}`
        }));
    }

    // ----------------------------------------------------------------- chart
    get chart() {
        const rows = (this.data && this.data.by_day) || [];
        const plotW = W - PAD.left - PAD.right;
        const plotH = H - PAD.top - PAD.bottom;
        const max = niceMax(Math.max(0, ...rows.map((r) => (r.requirement || 0) + (r.developer || 0))));
        const y = (v) => PAD.top + plotH - (v / max) * plotH;
        const band = plotW / Math.max(rows.length, 1);
        const barW = Math.min(34, band * 0.62);
        const every = Math.ceil(rows.length / 8);
        let peak = -1;
        let peakVal = 0;
        rows.forEach((r, i) => {
            const t = (r.requirement || 0) + (r.developer || 0);
            if (t > peakVal) {
                peakVal = t;
                peak = i;
            }
        });
        const bars = rows.map((r, i) => {
            const x = PAD.left + band * i + (band - barW) / 2;
            const req = r.requirement || 0;
            const dev = r.developer || 0;
            const hReq = (req / max) * plotH;
            const hDev = (dev / max) * plotH;
            const base = PAD.top + plotH;
            const reqTop = base - hReq;
            const devH = Math.max(0, hDev - (hReq > 0 && hDev > 0 ? GAP : 0));
            const devTop = reqTop - (hReq > 0 && hDev > 0 ? GAP : 0) - devH;
            return {
                key: r.date,
                index: i,
                reqPath: dev > 0 ? square(x, reqTop, barW, hReq) : topRounded(x, reqTop, barW, hReq, 4),
                devPath: topRounded(x, devTop, barW, devH, 4),
                hitX: PAD.left + band * i,
                hitW: band,
                showLabel: i % every === 0 || i === rows.length - 1,
                labelX: x + barW / 2,
                date: r.date.slice(5),
                peak: i === peak && peakVal > 0,
                peakLabel: short(peakVal),
                peakY: (dev > 0 ? devTop : reqTop) - 6,
                active: i === this.hoverIndex,
                hitClass: i === this.hoverIndex ? 'hit hit_active' : 'hit'
            };
        });
        const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({
            key: String(f),
            y: y(max * f),
            label: short(max * f)
        }));
        return { bars, ticks, plotTop: PAD.top, plotBottom: PAD.top + plotH, left: PAD.left, right: W - PAD.right };
    }

    get bars() {
        return this.chart.bars;
    }

    get ticks() {
        return this.chart.ticks.map((t) => ({ ...t, x1: PAD.left, x2: W - PAD.right, lx: PAD.left - 8, ly: t.y + 4 }));
    }

    get baselineY() {
        return this.chart.plotBottom;
    }

    get axisY() {
        return H - 10;
    }

    get reqColor() {
        return SERIES[0].color;
    }

    get devColor() {
        return SERIES[1].color;
    }

    handleBarEnter(event) {
        this.hoverIndex = Number(event.currentTarget.dataset.index);
    }

    handleBarLeave() {
        this.hoverIndex = -1;
    }

    get tooltip() {
        const rows = (this.data && this.data.by_day) || [];
        const r = rows[this.hoverIndex];
        if (!r) return null;
        const band = (W - PAD.left - PAD.right) / Math.max(rows.length, 1);
        const xPct = ((PAD.left + band * (this.hoverIndex + 0.5)) / W) * 100;
        const flip = xPct > 70;
        return {
            date: new Date(`${r.date}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }),
            req: fmt(r.requirement),
            dev: fmt(r.developer),
            total: fmt((r.requirement || 0) + (r.developer || 0)),
            style: flip ? `right:${100 - xPct + 2}%` : `left:${xPct + 2}%`
        };
    }

    get dayRows() {
        return ((this.data && this.data.by_day) || []).map((r) => ({
            key: r.date,
            date: r.date,
            req: fmt(r.requirement),
            dev: fmt(r.developer),
            total: fmt((r.requirement || 0) + (r.developer || 0))
        }));
    }

    // ---------------------------------------------------------------- tables
    get tickets() {
        const rows = (this.data && this.data.by_ticket) || [];
        const max = Math.max(1, ...rows.map((r) => r.total));
        return rows.map((r) => ({
            ...r,
            key: r.ticket,
            reqLabel: fmt(r.requirement),
            devLabel: fmt(r.developer),
            totalLabel: fmt(r.total),
            reqStyle: `width:${(r.requirement / max) * 100}%;background:${SERIES[0].color}`,
            devStyle: `width:${(r.developer / max) * 100}%;background:${SERIES[1].color}`
        }));
    }

    get developers() {
        const rows = (this.data && this.data.by_user) || [];
        const max = Math.max(1, ...rows.map((r) => r.total));
        return rows.map((r) => ({
            ...r,
            key: r.user,
            reqLabel: fmt(r.requirement),
            devLabel: fmt(r.developer),
            totalLabel: fmt(r.total),
            reqStyle: `width:${(r.requirement / max) * 100}%;background:${SERIES[0].color}`,
            devStyle: `width:${(r.developer / max) * 100}%;background:${SERIES[1].color}`
        }));
    }

    get hasDevelopers() {
        return this.developers.length > 0;
    }

    get hasTickets() {
        return this.tickets.length > 0;
    }

    get recent() {
        return ((this.data && this.data.recent) || []).map((r) => ({
            ...r,
            key: r.id,
            when: r.created_at ? new Date(r.created_at).toLocaleString() : '',
            agentLabel: r.agent === 'developer' ? 'Developer' : 'Requirement',
            agentStyle: `background:${r.agent === 'developer' ? SERIES[1].color : SERIES[0].color}`,
            inLabel: fmt(r.input_tokens),
            outLabel: fmt(r.output_tokens),
            totalLabel: fmt(r.total_tokens),
            statusClass: `status status_${r.status}`
        }));
    }

    get hasRecent() {
        return this.recent.length > 0;
    }

    get models() {
        return ((this.data && this.data.models) || []).map((m) => ({ key: m.model, text: `${m.model}: ${fmt(m.total_tokens)}` }));
    }

    get rangeLabel() {
        return this.data ? `${this.data.from} to ${this.data.to}` : '';
    }
}
