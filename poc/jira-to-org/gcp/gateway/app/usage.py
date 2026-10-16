"""Token usage across agent runs, shaped for the Agent Dashboard tab.

Every run that called a model carries a `usage` block (see RunContext.add_usage):
the Requirement agent's Responses API calls, and the Developer agent's
`codex exec` turns. This sums them per agent, per day, per ticket.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

AGENTS = ("requirement", "developer")
COUNTERS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens", "calls")


def _empty() -> dict:
    return {"runs": 0, "no_model_runs": 0, "credits_used": 0.0, "limit_pct_used": 0.0, **{k: 0 for k in COUNTERS}}


def summarize(runs: list[dict], days: int = 14, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    start = (now - timedelta(days=days - 1)).date()
    totals = {a: _empty() for a in AGENTS}
    by_day = {(start + timedelta(days=i)).isoformat(): {a: 0 for a in AGENTS} for i in range(days)}
    by_ticket: dict[str, dict] = defaultdict(lambda: {"requirement": 0, "developer": 0, "total": 0, "runs": 0})
    by_user: dict[str, dict] = defaultdict(lambda: {"requirement": 0, "developer": 0, "total": 0, "runs": 0})
    outcomes = {a: defaultdict(int) for a in AGENTS}
    models: dict[str, int] = defaultdict(int)
    recent = []
    for run in runs:
        u = run.get("usage")
        if not u or u.get("agent") not in AGENTS:
            continue
        day = (run.get("created_at") or "")[:10]
        if not day or day < start.isoformat():
            continue
        agent = u["agent"]
        t = totals[agent]
        t["runs"] += 1
        for k in COUNTERS:
            t[k] += int(u.get(k) or 0)
        if not u.get("calls"):
            t["no_model_runs"] += 1
        plan = run.get("plan_usage") or {}
        t["credits_used"] = round(t["credits_used"] + max(0.0, float(plan.get("credits_used") or 0)), 4)
        t["limit_pct_used"] = round(t["limit_pct_used"] + max(0.0, float(plan.get("primary_pct_used") or 0)), 2)
        outcomes[agent][run.get("status", "unknown")] += 1
        if day in by_day:
            by_day[day][agent] += int(u.get("total_tokens") or 0)
        ticket = u.get("ticket") or "(no ticket)"
        bt = by_ticket[ticket]
        bt[agent] += int(u.get("total_tokens") or 0)
        bt["total"] += int(u.get("total_tokens") or 0)
        bt["runs"] += 1
        who = (run.get("payload") or {}).get("user") or "(unknown)"
        bu = by_user[who]
        bu[agent] += int(u.get("total_tokens") or 0)
        bu["total"] += int(u.get("total_tokens") or 0)
        bu["runs"] += 1
        models[u.get("model") or "unknown"] += int(u.get("total_tokens") or 0)
        if len(recent) < 25:
            recent.append({"id": run.get("id"), "agent": agent, "ticket": u.get("ticket"), "status": run.get("status"),
                           "user": who,
                           "model": u.get("model"), "input_tokens": u.get("input_tokens", 0),
                           "output_tokens": u.get("output_tokens", 0), "total_tokens": u.get("total_tokens", 0),
                           "calls": u.get("calls", 0), "created_at": run.get("created_at"),
                           "cached_input_tokens": u.get("cached_input_tokens", 0),
                           "credits_used": plan.get("credits_used"), "limit_pct_used": plan.get("primary_pct_used")})
    for a in AGENTS:
        totals[a]["avg_per_run"] = round(totals[a]["total_tokens"] / totals[a]["runs"]) if totals[a]["runs"] else 0
        totals[a]["outcomes"] = dict(outcomes[a])
    grand = sum(totals[a]["total_tokens"] for a in AGENTS)
    return {
        "days": days,
        "from": start.isoformat(),
        "to": now.date().isoformat(),
        "total_tokens": grand,
        "agents": totals,
        "by_day": [{"date": d, **v} for d, v in by_day.items()],
        "by_ticket": sorted(({"ticket": k, **v} for k, v in by_ticket.items()), key=lambda r: -r["total"])[:20],
        "by_user": sorted(({"user": k, **v} for k, v in by_user.items()), key=lambda r: -r["total"])[:50],
        "models": [{"model": m, "total_tokens": n} for m, n in sorted(models.items(), key=lambda p: -p[1])],
        "recent": recent,
    }
