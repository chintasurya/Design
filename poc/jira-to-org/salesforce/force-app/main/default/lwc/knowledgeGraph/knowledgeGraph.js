import { LightningElement } from 'lwc';
import graphSchema from '@salesforce/apex/AgentConsoleController.graphSchema';
import graphNeighbourhood from '@salesforce/apex/AgentConsoleController.graphNeighbourhood';

// Node kinds in fixed categorical order (never cycled). Field and RecordType are
// structure, so they recede in neutral gray. Every node also carries a text label,
// so identity is never colour alone.
const KIND = {
    SObject: { color: '#2a78d6', label: 'Object' },
    ApexTrigger: { color: '#eb6834', label: 'Trigger' },
    ApexClass: { color: '#1baf7a', label: 'Apex class' },
    Flow: { color: '#eda100', label: 'Flow' },
    LWC: { color: '#e87ba4', label: 'LWC' },
    ValidationRule: { color: '#008300', label: 'Validation rule' },
    JiraTicket: { color: '#6250d6', label: 'Jira ticket' },
    Field: { color: '#a3a29b', label: 'Field' },
    RecordType: { color: '#c3c2b7', label: 'Record type' }
};
const ORDER = Object.keys(KIND);
const W = 960;
const H = 540;
const CX = W / 2;
const CY = H / 2;

const VERB = {
    SOBJECT_HAS_FIELD: 'has field',
    SOBJECT_HAS_RECORDTYPE: 'has record type',
    FIELD_REFERENCES_SOBJECT: 'looks up',
    TRIGGER_FIRES_ON_SOBJECT: 'fires on',
    TRIGGER_CALLS_APEX: 'calls',
    APEX_CALLS_APEX: 'calls',
    APEX_REFERENCES_SOBJECT: 'uses',
    APEX_REFERENCES_FIELD: 'uses field',
    FLOW_TRIGGERS_ON_SOBJECT: 'triggers on',
    FLOW_CREATES_SOBJECT: 'creates',
    FLOW_UPDATES_SOBJECT: 'updates',
    FLOW_READS_SOBJECT: 'reads',
    FLOW_CALLS_SUBFLOW: 'calls subflow',
    FLOW_CALLS_APEX: 'calls Apex',
    LWC_CALLS_APEX: 'calls Apex',
    VALIDATES_SOBJECT: 'validates',
    DEPENDS_ON: 'depends on',
    TICKET_MENTIONS: 'mentions',
    TICKET_IMPLEMENTED_BY: 'implemented by',
    TICKET_PARENT_OF: 'parent of',
    TICKET_LINKS_TO: 'links to'
};

function kind(type) {
    return KIND[type] || { color: '#a3a29b', label: type };
}

function errorText(e) {
    return (e && e.body && e.body.message) || (e && e.message) || String(e);
}

function fmt(n) {
    return Number(n || 0).toLocaleString();
}

// Arrowhead at (x2,y2) pointing along (x1,y1)->(x2,y2), pulled back by `gap` (the target's radius).
function arrow(x1, y1, x2, y2, gap) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len;
    const uy = dy / len;
    const tx = x2 - ux * gap;
    const ty = y2 - uy * gap;
    const s = 7;
    const p1 = `${tx},${ty}`;
    const p2 = `${tx - ux * s * 1.6 - uy * s},${ty - uy * s * 1.6 + ux * s}`;
    const p3 = `${tx - ux * s * 1.6 + uy * s},${ty - uy * s * 1.6 - ux * s}`;
    return `${p1} ${p2} ${p3}`;
}

export default class KnowledgeGraph extends LightningElement {
    viewBox = `0 0 ${W} ${H}`;
    mode = 'schema';
    loading = false;
    error;
    schema;
    ego;
    query = '';
    hover;

    connectedCallback() {
        this.loadSchema();
    }

    // ------------------------------------------------------------------ data
    async loadSchema() {
        this.loading = true;
        this.error = undefined;
        try {
            this.schema = JSON.parse(await graphSchema());
        } catch (e) {
            this.error = errorText(e);
        } finally {
            this.loading = false;
        }
    }

    async loadEgo(query, nodeId) {
        this.loading = true;
        this.error = undefined;
        this.hover = undefined;
        try {
            this.ego = JSON.parse(await graphNeighbourhood({ query: query || null, nodeId: nodeId || null }));
            this.mode = 'ego';
        } catch (e) {
            this.error = errorText(e);
        } finally {
            this.loading = false;
        }
    }

    handleQuery(event) {
        this.query = event.target.value;
    }

    handleQueryKey(event) {
        if (event.key === 'Enter') this.handleSearch();
    }

    handleSearch() {
        if (this.query.trim()) this.loadEgo(this.query.trim());
    }

    handleShowSchema() {
        this.mode = 'schema';
        this.hover = undefined;
        this.loadSchema();
    }

    handleNodeClick(event) {
        const id = event.currentTarget.dataset.id;
        if (this.mode === 'ego' && id && this.ego && id !== this.ego.centre) {
            this.loadEgo(null, id);
        } else if (this.mode === 'schema') {
            const type = event.currentTarget.dataset.type;
            if (type) this.hover = { title: kind(type).label, lines: this.typeLines(type) };
        }
    }

    handleMatch(event) {
        this.loadEgo(null, event.currentTarget.dataset.id);
    }

    handleEdgeEnter(event) {
        const idx = Number(event.currentTarget.dataset.index);
        const list = this.mode === 'schema' ? this.schemaLayout.links : this.egoLayout.links;
        const link = list[idx];
        if (link) this.hover = { title: link.title, lines: link.lines };
    }

    handleNodeEnter(event) {
        const idx = Number(event.currentTarget.dataset.index);
        const list = this.mode === 'schema' ? this.schemaLayout.nodes : this.egoLayout.nodes;
        const n = list[idx];
        if (n) this.hover = { title: n.title, lines: n.lines };
    }

    handleLeave() {
        this.hover = undefined;
    }

    // --------------------------------------------------------------- getters
    get isSchema() {
        return this.mode === 'schema';
    }

    get isEgo() {
        return this.mode === 'ego' && !!this.ego;
    }

    get hasHover() {
        return !!this.hover;
    }

    get hoverLines() {
        return ((this.hover && this.hover.lines) || []).map((text, i) => ({ key: String(i), text }));
    }

    get snapshotLabel() {
        const s = this.schema || {};
        const snap = s.snapshot || {};
        if (!s.nodes) return 'The graph has not been built yet. Use Rebuild knowledge graph on the Agent Console tab.';
        const built = snap.built_at ? ` · snapshot ${snap.snapshot_id} built ${new Date(snap.built_at).toLocaleString()}` : '';
        return `${fmt(s.nodes)} nodes · ${fmt(s.edges)} edges${built}`;
    }

    get notes() {
        return ((this.schema && this.schema.notes) || []).map((text, i) => ({ key: String(i), text }));
    }

    get hasNotes() {
        return this.notes.length > 0;
    }

    get legend() {
        const counts = {};
        ((this.schema && this.schema.node_types) || []).forEach((t) => {
            counts[t.type] = t.count;
        });
        return ORDER.filter((t) => counts[t]).map((t) => ({
            key: t,
            label: `${kind(t).label} · ${fmt(counts[t])}`,
            style: `background:${kind(t).color}`
        }));
    }

    typeLines(type) {
        const edges = (this.schema && this.schema.edge_types) || [];
        return edges
            .filter((e) => e.from_type === type || e.to_type === type)
            .map((e) => `${kind(e.from_type).label} ${VERB[e.edge_type] || e.edge_type} ${kind(e.to_type).label}: ${fmt(e.count)}`);
    }

    // Type-level map: one circle per kind of node, one curve per (from kind, to kind).
    get schemaLayout() {
        const s = this.schema;
        if (!s || !s.node_types || !s.node_types.length) return { nodes: [], links: [] };
        const types = ORDER.filter((t) => s.node_types.some((n) => n.type === t)).concat(
            s.node_types.map((n) => n.type).filter((t) => !ORDER.includes(t))
        );
        const count = {};
        s.node_types.forEach((n) => {
            count[n.type] = n.count;
        });
        const max = Math.max(...Object.values(count));
        const pos = {};
        types.forEach((t, i) => {
            const a = -Math.PI / 2 + (2 * Math.PI * i) / types.length;
            pos[t] = {
                x: CX + Math.cos(a) * 340,
                y: CY + Math.sin(a) * 200,
                r: 16 + 26 * Math.sqrt(count[t] / max)
            };
        });
        const pairs = {};
        (s.edge_types || []).forEach((e) => {
            const k = `${e.from_type}>${e.to_type}`;
            pairs[k] = pairs[k] || { from: e.from_type, to: e.to_type, count: 0, lines: [] };
            pairs[k].count += e.count;
            pairs[k].lines.push(`${VERB[e.edge_type] || e.edge_type}: ${fmt(e.count)}`);
        });
        const maxLink = Math.max(1, ...Object.values(pairs).map((p) => p.count));
        const links = Object.values(pairs).map((p, i) => {
            const a = pos[p.from];
            const b = pos[p.to];
            const width = 1.5 + 3 * (Math.log10(p.count + 1) / Math.log10(maxLink + 1));
            const title = `${kind(p.from).label} → ${kind(p.to).label} · ${fmt(p.count)}`;
            if (!a || !b) return null;
            if (p.from === p.to) {
                const d = `M ${a.x - 10} ${a.y - a.r} C ${a.x - 50} ${a.y - a.r - 60}, ${a.x + 50} ${a.y - a.r - 60}, ${a.x + 10} ${a.y - a.r}`;
                return { key: `l${i}`, index: i, d, width, title, lines: p.lines, label: fmt(p.count),
                    lx: a.x, ly: a.y - a.r - 50, head: arrow(a.x + 30, a.y - a.r - 30, a.x + 10, a.y - a.r, 0) };
            }
            // bend each direction to its own side so A->B and B->A never overlap
            const mx = (a.x + b.x) / 2;
            const my = (a.y + b.y) / 2;
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const len = Math.hypot(dx, dy) || 1;
            const bend = 0.18 * len;
            const qx = mx - (dy / len) * bend;
            const qy = my + (dx / len) * bend;
            return {
                key: `l${i}`,
                index: i,
                d: `M ${a.x} ${a.y} Q ${qx} ${qy} ${b.x} ${b.y}`,
                width,
                title,
                lines: p.lines,
                label: fmt(p.count),
                lx: (a.x + 2 * qx + b.x) / 4,
                ly: (a.y + 2 * qy + b.y) / 4,
                head: arrow(qx, qy, b.x, b.y, b.r + 2)
            };
        }).filter(Boolean);
        const nodes = types.map((t, i) => ({
            key: t,
            index: i,
            id: '',
            type: t,
            x: pos[t].x,
            y: pos[t].y,
            r: pos[t].r,
            fill: kind(t).color,
            label: kind(t).label,
            sub: fmt(count[t]),
            labelY: pos[t].y + pos[t].r + 16,
            subY: pos[t].y + pos[t].r + 30,
            title: `${kind(t).label} · ${fmt(count[t])}`,
            lines: this.typeLines(t)
        }));
        return { nodes, links };
    }

    // One component and its direct connections, grouped round it by kind.
    get egoLayout() {
        const g = this.ego;
        if (!g || !g.nodes) return { nodes: [], links: [] };
        const centre = g.nodes.find((n) => n.id === g.centre);
        const others = g.nodes
            .filter((n) => n.id !== g.centre)
            .sort((a, b) => ORDER.indexOf(a.type) - ORDER.indexOf(b.type) || a.label.localeCompare(b.label));
        const pos = { [centre.id]: { x: CX, y: CY, r: 30 } };
        others.forEach((n, i) => {
            const a = -Math.PI / 2 + (2 * Math.PI * i) / Math.max(others.length, 1);
            pos[n.id] = { x: CX + Math.cos(a) * 330, y: CY + Math.sin(a) * 200, r: 13 };
        });
        const pairs = {};
        g.edges.forEach((e) => {
            const other = e.from === g.centre ? e.to : e.from;
            pairs[other] = pairs[other] || { other, out: e.from === g.centre, lines: [] };
            const a = g.nodes.find((n) => n.id === e.from);
            const b = g.nodes.find((n) => n.id === e.to);
            pairs[other].lines.push(`${a ? a.label : e.from} ${VERB[e.type] || e.type} ${b ? b.label : e.to}` +
                (e.origin && e.origin !== 'ingest' ? ` (${e.origin})` : ''));
        });
        const links = Object.values(pairs).filter((p) => pos[p.other]).map((p, i) => {
            const a = pos[g.centre];
            const b = pos[p.other];
            const [from, to] = p.out ? [a, b] : [b, a];
            return {
                key: `e${i}`,
                index: i,
                d: `M ${from.x} ${from.y} L ${to.x} ${to.y}`,
                width: 1.5,
                title: p.lines[0],
                lines: p.lines,
                label: '',
                lx: 0,
                ly: 0,
                head: arrow(from.x, from.y, to.x, to.y, to.r + 2)
            };
        });
        const all = [centre, ...others];
        const nodes = all.map((n, i) => {
            const p = pos[n.id];
            const props = Object.entries(n.properties || {}).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`);
            return {
                key: n.id,
                index: i,
                id: n.id,
                type: n.type,
                x: p.x,
                y: p.y,
                r: p.r,
                fill: kind(n.type).color,
                label: n.label.length > 34 ? `${n.label.slice(0, 33)}…` : n.label,
                sub: kind(n.type).label,
                labelY: p.y + p.r + 15,
                subY: p.y + p.r + 28,
                title: `${kind(n.type).label}: ${n.label}`,
                lines: [`${n.degree} connections in the graph`, ...props, n.id === g.centre ? '' : 'Click to centre on it'].filter(Boolean)
            };
        });
        return { nodes, links };
    }

    get schemaNodes() {
        return this.schemaLayout.nodes;
    }

    get schemaLinks() {
        return this.schemaLayout.links;
    }

    get egoNodes() {
        return this.egoLayout.nodes;
    }

    get egoLinks() {
        return this.egoLayout.links;
    }

    get egoTitle() {
        if (!this.ego) return '';
        const c = this.ego.nodes.find((n) => n.id === this.ego.centre);
        const folded = this.ego.fields_folded ? ` · ${fmt(this.ego.fields_folded)} fields not drawn` : '';
        return `${kind(c.type).label}: ${c.label} · ${this.ego.nodes.length - 1} direct connections${folded}`;
    }

    get matches() {
        return ((this.ego && this.ego.matches) || [])
            .filter((m) => m.id !== this.ego.centre)
            .map((m) => ({ ...m, text: `${kind(m.type).label}: ${m.label}` }));
    }

    get hasMatches() {
        return this.matches.length > 0;
    }

    get schemaRows() {
        return ((this.schema && this.schema.edge_types) || []).map((e, i) => ({
            key: String(i),
            from: kind(e.from_type).label,
            verb: VERB[e.edge_type] || e.edge_type,
            to: kind(e.to_type).label,
            count: fmt(e.count)
        }));
    }
}
