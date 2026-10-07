"""Digest a Query Killer slow-query incident into a compact report.

Usage:
    python3 slow_query_report.py --bundle bundle.json [--mode triage|deep] [--format md|json|html] [--out FILE]
    python3 slow_query_report.py --fetch --sentry-short-id RAILS-BACKEND-4FA7 --pd-incident Q25ND367948EA8 \
        --bundle-out bundle.json

Why this exists: a Sentry issue with hundreds of events is megabytes of JSON. Reading
it into an agent context to count shards is wasteful and error-prone. This script does
the counting deterministically and emits ~40 lines the agent can actually reason over.

The evidence rules are deliberately conservative — "scatter-gather" is only claimed
when a confirmed shard key is absent from the filter AND multiple shards were observed
running the same signature concurrently. Everything weaker is reported as weaker.

Pure analysis/rendering helpers live at module scope and are unit-tested.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

SEVERITY_ORDER = ["low", "medium", "high", "critical"]

# Status palette (fixed, never themed) — always shipped with an icon + text label.
SEVERITY_STYLE = {
    "low": ("#0ca30c", "●"),
    "medium": ("#fab219", "▲"),
    "high": ("#ec835a", "◆"),
    "critical": ("#d03b3b", "⬣"),
}

# Signals are checked in priority order; `source` is the killer's own attribution.
ORIGIN_SIGNALS = ["source", "app_name", "transaction", "server_name", "client"]

ORIGIN_PATTERNS = [
    ("manual-console", r"rails\s+runner|\brake\b|\bconsole\b|\birb\b|^bin/|^script/|Rails::Console|mongosh|mongo\s+shell"),
    ("scheduled", r"Clockwork|[Cc]ron|Scheduler|Sidekiq::Scheduled|periodic"),
    ("background-job", r"(Worker|Job)\b|Sidekiq|^sidekiq|resque|delayed_job"),
    ("user-request", r"Controller[#/]|Controller$|^GET\s|^POST\s|^/|puma|unicorn|Grape::"),
]

ORIGIN_MEANING = {
    "user-request": "a user was waiting on this — customer-visible latency, page-worthy",
    "background-job": "a queued worker ran it — retry storms and queue backup are the risk, not user latency",
    "scheduled": "a scheduled job ran it — predictable, can be moved off-peak",
    "manual-console": "a human ran this by hand — usually a backfill/one-off, not a product defect",
    "unknown": "origin could not be attributed from the available signals",
}

# Fan-out below this many concurrent shards is not, on its own, evidence of a scatter-gather.
CONCURRENCY_PROOF_THRESHOLD = 2
DEPLOY_WINDOW_MINUTES = 120
MAX_TIMELINE_BARS = 48


# --------------------------------------------------------------------------- parsing


def parse_ts(value):
    """Parse an ISO-8601 timestamp (Sentry/PD style, with or without `Z`) to aware UTC."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_shard(opid):
    """`contacts-16:-819763575` -> `contacts-16`. Returns None when the opid has no shard prefix."""
    if not opid or ":" not in str(opid):
        return None
    shard = str(opid).split(":", 1)[0].strip()
    return shard or None


def filter_keys(filter_value):
    """Top-level field names a Mongo filter document constrains, `$and`/`$or` flattened."""
    keys = []

    def walk(node):
        if isinstance(node, dict):
            for key, val in node.items():
                if key in ("$and", "$or", "$nor"):
                    walk(val)
                elif not key.startswith("$"):
                    keys.append(key)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    if isinstance(filter_value, str):
        try:
            filter_value = json.loads(filter_value)
        except (ValueError, TypeError):
            return []
    walk(filter_value)
    seen = []
    for key in keys:
        if key not in seen:
            seen.append(key)
    return seen


def op_interval(event):
    """(start, end) for one sampled op. End is the sample time; start is end - secs_running."""
    end = parse_ts(event.get("dateCreated") or event.get("timestamp"))
    if end is None:
        return None
    try:
        secs = float(event.get("context", {}).get("secs_running") or 0.0)
    except (TypeError, ValueError):
        secs = 0.0
    return (end - timedelta(seconds=max(secs, 0.0)), end)


# --------------------------------------------------------------------------- evidence


def classify_origin(signals):
    """Attribute an op to user-request / background-job / scheduled / manual-console.

    Returns (origin, confidence, evidence). Confidence is `high` when a second signal
    agrees with the first, `low` when one contradicts it, `medium` on a lone signal.
    """
    hits = []
    for name in ORIGIN_SIGNALS:
        value = signals.get(name)
        if not value:
            continue
        for origin, pattern in ORIGIN_PATTERNS:
            if re.search(pattern, str(value)):
                hits.append((name, origin, str(value)))
                break
    if not hits:
        return "unknown", "none", []
    primary = hits[0][1]
    agree = [h for h in hits[1:] if h[1] == primary]
    disagree = [h for h in hits[1:] if h[1] != primary]
    if disagree:
        confidence = "low"
    elif agree:
        confidence = "high"
    else:
        confidence = "medium"
    evidence = ["{}={} -> {}".format(name, value, origin) for name, origin, value in hits]
    return primary, confidence, evidence


def peak_concurrency(intervals):
    """Max number of *distinct shards* running at one instant, and when.

    intervals: list of (start, end, shard). This is the fan-out proof — many shards
    over an hour could be sequential retries; many shards at one instant cannot be.
    """
    usable = [i for i in intervals if i[0] and i[1] and i[2]]
    if not usable:
        return 0, None, []
    best_count, best_at, best_shards = 0, None, []
    for start, _end, _shard in usable:
        active = {s for (st, en, s) in usable if st <= start <= en}
        if len(active) > best_count:
            best_count, best_at, best_shards = len(active), start, sorted(active)
    return best_count, best_at, best_shards


def fanout_evidence(events):
    """Shard fan-out evidence for the dominant query signature."""
    sigs = {}
    for event in events:
        ctx = event.get("context", {}) or {}
        sigs.setdefault(ctx.get("signature") or "unknown", []).append(event)
    signature = max(sigs, key=lambda k: len(sigs[k]))
    group = sigs[signature]

    intervals, shards, opids = [], set(), set()
    for event in group:
        ctx = event.get("context", {}) or {}
        shard = parse_shard(ctx.get("opid"))
        if ctx.get("opid"):
            opids.add(ctx["opid"])
        if shard:
            shards.add(shard)
        span = op_interval(event)
        if span and shard:
            intervals.append((span[0], span[1], shard))

    concurrent, at, concurrent_shards = peak_concurrency(intervals)

    if not shards:
        verdict = "unknown"
        basis = "no opid on any event — shard attribution unavailable"
    elif len(shards) < 2:
        verdict = "single-shard"
        basis = "all {} events on shard {}".format(len(group), sorted(shards)[0])
    elif concurrent >= CONCURRENCY_PROOF_THRESHOLD:
        verdict = "proven"
        basis = "{} distinct shards running signature `{}` simultaneously at {} ({})".format(
            concurrent,
            signature,
            at.strftime("%Y-%m-%dT%H:%M:%SZ") if at else "?",
            ", ".join(concurrent_shards),
        )
    else:
        verdict = "likely"
        basis = "{} distinct shards seen across {} events, but no two op windows overlap — could be sequential".format(
            len(shards), len(group)
        )

    return {
        "signature": signature,
        "events_in_signature": len(group),
        "distinct_shards": len(shards),
        "shards": sorted(shards),
        "distinct_opids": len(opids),
        "peak_concurrent_shards": concurrent,
        "peak_at": at.strftime("%Y-%m-%dT%H:%M:%SZ") if at else None,
        "peak_shards": concurrent_shards,
        "verdict": verdict,
        "basis": basis,
        "intervals": intervals,
    }


def classify_pattern(fanout, filter_fields, shard_key, shard_key_source):
    """Name the access pattern without overstating it.

    `scatter-gather` requires BOTH a confirmed shard key absent from the filter AND
    proven/likely multi-shard execution. Anything less is reported as what it is.
    """
    confirmed = bool(shard_key) and shard_key_source not in (None, "", "unconfirmed", "assumed")
    covers = confirmed and any(k in filter_fields for k in shard_key)
    multi = fanout["verdict"] in ("proven", "likely")
    key_text = ", ".join(shard_key)
    filter_text = ", ".join(filter_fields)

    if not confirmed:
        if multi:
            return {
                "pattern": "multi-shard fan-out",
                "confidence": "provisional",
                "why": "query ran on {} shards, but the shard key for the collection is unconfirmed — "
                "cannot call this a shard-key mismatch yet".format(fanout["distinct_shards"]),
            }
        return {
            "pattern": "indeterminate",
            "confidence": "provisional",
            "why": "shard key unconfirmed and no multi-shard evidence",
        }
    if covers:
        return {
            "pattern": "targeted (large shard)",
            "confidence": "high",
            "why": "filter includes shard key {} — Mongos targets a shard; slowness is volume or plan, not routing".format(
                key_text
            ),
        }
    if multi:
        return {
            "pattern": "scatter-gather",
            "confidence": "high" if fanout["verdict"] == "proven" else "medium",
            "why": "collection sharded by {}; filter constrains {} — no shard can be targeted, so the op fans out".format(
                key_text, filter_text or "nothing"
            ),
        }
    return {
        "pattern": "shard-key mismatch (fan-out unobserved)",
        "confidence": "medium",
        "why": "filter omits shard key {}, but only one shard was observed — mismatch is structural, fan-out is not yet demonstrated".format(
            key_text
        ),
    }


def correlate_deploys(first_seen, deploys, issue_first_release, window_minutes=DEPLOY_WINDOW_MINUTES, events=None):
    """Decide whether a deploy plausibly introduced this slow query."""
    first_seen = parse_ts(first_seen)
    parsed = []
    for dep in deploys or []:
        when = parse_ts(dep.get("dateFinished") or dep.get("dateStarted") or dep.get("finished_at"))
        if when:
            parsed.append({"version": dep.get("version"), "at": when, "url": dep.get("url")})
    parsed.sort(key=lambda d: d["at"])

    result = {
        "verdict": "no-deploy-data",
        "nearest": None,
        "lag_minutes": None,
        "note": "no deploy records supplied — deploy correlation not evaluated",
        "events_before": None,
        "events_after": None,
    }
    if not parsed or not first_seen:
        return result

    prior = [d for d in parsed if d["at"] <= first_seen]
    if not prior:
        result["verdict"] = "no-deploy-before-onset"
        result["note"] = "no deploy landed before first_seen — onset is not deploy-driven"
        return result

    nearest = prior[-1]
    lag = (first_seen - nearest["at"]).total_seconds() / 60.0
    result["nearest"] = {
        "version": nearest["version"],
        "at": nearest["at"].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "url": nearest["url"],
    }
    result["lag_minutes"] = round(lag, 1)

    if events:
        before = sum(1 for e in events if (parse_ts(e.get("dateCreated")) or first_seen) < nearest["at"])
        result["events_before"] = before
        result["events_after"] = len(events) - before

    within = lag <= window_minutes
    if issue_first_release and nearest["version"] and issue_first_release != nearest["version"]:
        result["verdict"] = "pre-existing"
        result["note"] = "issue first appeared in release {}, not the deploy that preceded onset ({}) — not a new regression".format(
            issue_first_release, nearest["version"]
        )
    elif within and issue_first_release and nearest["version"] and issue_first_release == nearest["version"]:
        result["verdict"] = "deploy-correlated"
        result["note"] = "first seen {:.0f} min after {} shipped, and the issue's first release IS that version — treat as a regression and check the diff".format(
            lag, nearest["version"]
        )
    elif within:
        result["verdict"] = "deploy-adjacent"
        result["note"] = "first seen {:.0f} min after {} shipped, but release provenance is unconfirmed — timing only".format(
            lag, nearest["version"]
        )
    else:
        result["verdict"] = "pre-existing"
        result["note"] = "nearest prior deploy ({}) was {:.0f} min before onset, outside the {}-min window".format(
            nearest["version"], lag, window_minutes
        )
    return result


def blast_radius(events):
    """Single-account vs fleet, one-window vs recurring."""
    accounts, days, times = set(), set(), []
    for event in events:
        ctx = event.get("context", {}) or {}
        for key in ("account_id", "team_id", "tenant_id"):
            for field in filter_keys_values(ctx.get("filter"), key):
                accounts.add(field)
        when = parse_ts(event.get("dateCreated"))
        if when:
            days.add(when.date())
            times.append(when)
    radius = "single-account" if len(accounts) <= 1 else "fleet"
    temporality = "recurring" if len(days) > 1 else "one-window"
    return {
        "radius": radius,
        "temporality": temporality,
        "distinct_accounts": len(accounts),
        "accounts": sorted(str(a) for a in accounts)[:5],
        "distinct_days": len(days),
        "first": min(times).strftime("%Y-%m-%dT%H:%M:%SZ") if times else None,
        "last": max(times).strftime("%Y-%m-%dT%H:%M:%SZ") if times else None,
    }


def filter_keys_values(filter_value, key):
    """Every literal value a filter binds to `key` (handles `$in`, `$eq`, bare equality)."""
    if isinstance(filter_value, str):
        try:
            filter_value = json.loads(filter_value)
        except (ValueError, TypeError):
            return []
    out = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == key:
                    if isinstance(v, dict):
                        for op in ("$in", "$eq"):
                            if op in v:
                                out.extend(v[op] if isinstance(v[op], list) else [v[op]])
                    elif isinstance(v, list):
                        out.extend(v)
                    else:
                        out.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(filter_value)
    return out


def max_in_size(filter_value):
    """Largest `$in` array in the filter — a big one multiplies index seeks per shard."""
    if isinstance(filter_value, str):
        try:
            filter_value = json.loads(filter_value)
        except (ValueError, TypeError):
            return 0
    largest = 0

    def walk(node):
        nonlocal largest
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$in" and isinstance(v, list):
                    largest = max(largest, len(v))
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(filter_value)
    return largest


def fmt_secs(value):
    """`71.61684` -> `71.6`. Full precision is noise in a headline figure."""
    try:
        return "{:.1f}".format(float(value))
    except (TypeError, ValueError):
        return str(value)


def bump(severity, steps=1):
    idx = min(SEVERITY_ORDER.index(severity) + steps, len(SEVERITY_ORDER) - 1)
    return SEVERITY_ORDER[idx]


def propose_severity(radius, temporality, pattern, kill_succeeded, deploy_verdict, origin):
    """Base matrix, then modifiers. Returns (severity, reasons, provisional)."""
    structural = pattern["pattern"] in ("scatter-gather", "multi-shard fan-out", "shard-key mismatch (fan-out unobserved)")
    reasons = []

    if radius == "fleet" and temporality == "recurring" and structural:
        severity = "high"
        reasons.append("fleet-wide + recurring + structural")
    elif temporality == "recurring" and structural:
        severity = "medium"
        reasons.append("structural cause, bounded blast radius")
    elif structural:
        severity = "low"
        reasons.append("structural but one window, one tenant")
    else:
        severity = "low"
        reasons.append("no structural cause established")

    if kill_succeeded:
        severity = bump(severity)
        reasons.append("kill succeeded — raise one level and open a data-integrity check")
    if deploy_verdict == "deploy-correlated":
        severity = bump(severity)
        reasons.append("deploy-correlated regression — a revert may be the fastest fix")
    if origin == "manual-console" and radius == "single-account" and temporality == "one-window":
        severity = "low"
        reasons.append("manually-run op — alert-tuning candidate, not a product defect")

    provisional = pattern["confidence"] == "provisional"
    return severity, reasons, provisional


# --------------------------------------------------------------------------- advice


def recommendations(digest):
    """Ranked, fact-gated remediation ladder. Only rules whose preconditions hold are emitted."""
    ctx = digest["op"]
    origin = digest["origin"]["origin"]
    pattern = digest["pattern"]["pattern"]
    plan = (ctx.get("plan_summary") or "").upper()
    shard_key = digest["shard_key"]["key"]
    in_size = max_in_size(ctx.get("filter"))
    out = []

    def add(tier, action, why, effort, owner):
        out.append({"tier": tier, "action": action, "why": why, "effort": effort, "owner": owner})

    if origin == "manual-console":
        add(
            "process",
            "Wrap ad-hoc queries in a backfill runbook: `maxTimeMS`, batch size, secondary read preference, off-peak window",
            "A hand-run op paged production. The code is not necessarily wrong — the way it was run is.",
            "S",
            "whoever ran it",
        )
        add(
            "alerting",
            "Exclude console/rake origins from the Query Killer page, or route them to a non-paging lane",
            "Paging on-call for a human-initiated query trains alert fatigue.",
            "S",
            "DevOps",
        )
    if pattern == "scatter-gather" and shard_key:
        add(
            "query-shape",
            "Add shard key `{}` to the filter so Mongos targets one shard".format(", ".join(shard_key)),
            "This is the single highest-leverage change: it converts an N-shard fan-out into a 1-shard read.",
            "M",
            "owning team",
        )
    if pattern in ("multi-shard fan-out", "shard-key mismatch (fan-out unobserved)"):
        add(
            "verify",
            "Confirm the collection's shard key (`sh.status()` / `config.collections`) before committing to a fix",
            "Every remediation below branches on the shard key; guessing it wastes a sprint.",
            "S",
            "DBA / mongo-specialist",
        )
    if "COLLSCAN" in plan:
        add(
            "index",
            "No usable index — add one (see `apollo-eng-devops:create-mongo-index`)",
            "COLLSCAN means every document is read; an index is the fix before anything structural.",
            "M",
            "owning team",
        )
    elif "IXSCAN" in plan and pattern == "scatter-gather":
        add(
            "index",
            "Do NOT add another index on the filter field — extend the existing index to be shard-key-prefixed instead",
            "The plan is already `{}`. Each shard uses the index and is still slow; more indexes add write cost, not speed.".format(
                ctx.get("plan_summary")
            ),
            "M",
            "owning team",
        )
    if in_size > 25:
        add(
            "access-pattern",
            "Chunk the {}-element `$in` list into batches".format(in_size),
            "A large `$in` multiplies index seeks per shard and defeats plan caching.",
            "S",
            "owning team",
        )
    add(
        "guardrail",
        "Set `maxTimeMS` on this query path below the Query Killer threshold",
        "The op then self-cancels with a catchable error instead of running long enough to page — this is the fastest way to stop the alert without changing the data model.",
        "S",
        "owning team",
    )
    if digest["blast"]["temporality"] == "recurring" or digest["blast"]["radius"] == "fleet":
        add(
            "architecture",
            "Precompute or cache this aggregate rather than computing it per request",
            "A repeated fan-out is a read-model problem; caching removes the query rather than tuning it.",
            "L",
            "owning team",
        )
    if origin == "user-request":
        add(
            "access-pattern",
            "Move the read off the request path (async job + polling) or paginate it",
            "A multi-second read on a user request is a timeout risk regardless of how well it is indexed.",
            "M",
            "owning team",
        )
    if digest["deploy"]["verdict"] == "deploy-correlated":
        add(
            "regression",
            "Diff release {} for changes to this query path; a revert may beat a forward fix".format(
                digest["deploy"]["nearest"]["version"]
            ),
            "Onset lines up with the deploy and the issue is new in that release.",
            "S",
            "release owner",
        )
    for rank, item in enumerate(out, 1):
        item["rank"] = rank
    return out


# --------------------------------------------------------------------------- digest


def build_digest(bundle, shard_key=None, shard_key_source=None):
    """Turn a raw Sentry/PD/deploy bundle into the compact structure everything else renders."""
    issue = bundle.get("sentry_issue", {}) or {}
    events = bundle.get("sentry_events", []) or []
    pd = bundle.get("pagerduty", {}) or {}
    sk = bundle.get("shard_key", {}) or {}
    shard_key = shard_key or sk.get("key") or []
    if isinstance(shard_key, str):
        shard_key = [shard_key]
    shard_key_source = shard_key_source or sk.get("source") or "unconfirmed"

    latest = events[0] if events else {}
    ctx = latest.get("context", {}) or {}
    tags = latest.get("tags", {}) or {}
    fields = filter_keys(ctx.get("filter"))

    fanout = fanout_evidence(events) if events else {
        "signature": "unknown", "events_in_signature": 0, "distinct_shards": 0, "shards": [],
        "distinct_opids": 0, "peak_concurrent_shards": 0, "peak_at": None, "peak_shards": [],
        "verdict": "unknown", "basis": "no events", "intervals": [],
    }
    origin, confidence, evidence = classify_origin({
        "source": ctx.get("source"),
        "app_name": ctx.get("appName") or ctx.get("app_name"),
        "transaction": latest.get("transaction") or tags.get("transaction"),
        "server_name": tags.get("server_name"),
        "client": ctx.get("client"),
    })
    pattern = classify_pattern(fanout, fields, shard_key, shard_key_source)
    deploy = correlate_deploys(
        issue.get("firstSeen"),
        bundle.get("deploys"),
        (issue.get("firstRelease") or {}).get("version") if isinstance(issue.get("firstRelease"), dict) else issue.get("firstRelease"),
        events=events,
    )
    blast = blast_radius(events)
    kill_succeeded = str(ctx.get("kill_succeeded")).lower() == "true"
    severity, reasons, provisional = propose_severity(
        blast["radius"], blast["temporality"], pattern, kill_succeeded, deploy["verdict"], origin
    )

    digest = {
        "meta": bundle.get("meta", {}),
        "incident": {
            "pd_id": pd.get("id"),
            "pd_number": pd.get("incident_number"),
            "pd_title": pd.get("title"),
            "pd_urgency": pd.get("urgency"),
            "pd_service": pd.get("service"),
            "pd_url": pd.get("html_url"),
            "sentry_short_id": issue.get("shortId"),
            "sentry_id": issue.get("id"),
            "sentry_url": issue.get("permalink"),
            "event_count": issue.get("count"),
            "first_seen": issue.get("firstSeen"),
            "last_seen": issue.get("lastSeen"),
            "events_sampled": len(events),
        },
        "op": {
            "source": ctx.get("source", "absent"),
            "collection": ctx.get("collection", "absent"),
            "filter": ctx.get("filter", "absent"),
            "filter_fields": fields,
            "signature": ctx.get("signature", "absent"),
            "secs_running": ctx.get("secs_running", "absent"),
            "opid": ctx.get("opid", "absent"),
            "shard": parse_shard(ctx.get("opid")) or "absent",
            "plan_summary": ctx.get("plan_summary", "absent"),
            "kill_attempted": ctx.get("kill_attempted", "absent"),
            "kill_succeeded": ctx.get("kill_succeeded", "absent"),
        },
        "origin": {"origin": origin, "confidence": confidence, "evidence": evidence, "meaning": ORIGIN_MEANING[origin]},
        "fanout": {k: v for k, v in fanout.items() if k != "intervals"},
        "shard_key": {"key": shard_key, "source": shard_key_source, "confirmed": shard_key_source not in ("unconfirmed", "assumed", "", None)},
        "pattern": pattern,
        "deploy": deploy,
        "blast": blast,
        "severity": {"proposed": severity, "reasons": reasons, "provisional": provisional},
        "_intervals": fanout.get("intervals", []),
    }
    digest["recommendations"] = recommendations(digest)
    return digest


# --------------------------------------------------------------------------- render


def render_markdown(digest, mode="triage"):
    d = digest
    inc, op, sev = d["incident"], d["op"], d["severity"]
    lines = []
    prov = " (provisional)" if sev["provisional"] else ""
    lines.append("## Slow query triage — {} / {}".format(inc.get("sentry_short_id") or "?", inc.get("pd_id") or "?"))
    src = d["meta"].get("source", "unspecified")
    if src != "live":
        lines.append("> Data source: **{}** — {}".format(src, d["meta"].get("notes", "not a live fetch")))
    lines.append("")
    lines.append("**Verdict:** {} / {} / {} · severity **{}**{}".format(
        d["blast"]["radius"], d["blast"]["temporality"], d["pattern"]["pattern"], sev["proposed"], prov))
    lines.append("")
    lines.append("| field | value |")
    lines.append("| --- | --- |")
    lines.append("| Origin | **{}** ({} confidence) — {} |".format(
        d["origin"]["origin"], d["origin"]["confidence"], d["origin"]["meaning"]))
    lines.append("| Deploy | **{}** — {} |".format(d["deploy"]["verdict"], d["deploy"]["note"]))
    lines.append("| Fan-out | **{}** — {} |".format(d["fanout"]["verdict"], d["fanout"]["basis"]))
    lines.append("| Shard key | {} (source: {}) |".format(
        ", ".join(d["shard_key"]["key"]) or "unknown", d["shard_key"]["source"]))
    lines.append("| Runtime | {}s on {} |".format(op["secs_running"], op["shard"]))
    lines.append("| Window | {} – {} ({} events, {} sampled) |".format(
        inc["first_seen"], inc["last_seen"], inc["event_count"], inc["events_sampled"]))
    lines.append("| Killer | kill_attempted={} kill_succeeded={} |".format(op["kill_attempted"], op["kill_succeeded"]))
    lines.append("| Plan | `{}` |".format(op["plan_summary"]))
    lines.append("")
    lines.append("**Why this severity:** " + "; ".join(sev["reasons"]) + ".")
    lines.append("")

    top = d["recommendations"] if mode == "deep" else d["recommendations"][:3]
    lines.append("### Recommendations" + ("" if mode == "deep" else " (top 3 — run `--mode deep` for the full ladder)"))
    lines.append("")
    lines.append("| # | tier | action | why | effort |")
    lines.append("| --- | --- | --- | --- | --- |")
    for rec in top:
        lines.append("| {} | {} | {} | {} | {} |".format(
            rec["rank"], rec["tier"], rec["action"], rec["why"], rec["effort"]))
    lines.append("")

    if str(op["kill_succeeded"]).lower() == "true":
        lines.append("> **kill_succeeded=true** — a mid-flight op was aborted. Open a data-integrity check. [HUMAN]")
        lines.append("")
    lines.append("> Kill/no-kill on any live op is **[HUMAN] only** — this report never proposes one.")

    if mode == "deep":
        lines.append("")
        lines.append("### Shards touched")
        lines.append("")
        lines.append("{} distinct: {}".format(d["fanout"]["distinct_shards"], ", ".join(d["fanout"]["shards"]) or "none"))
        lines.append("")
        lines.append("### Drafted ticket (not filed)")
        lines.append("")
        lines.append("```text")
        lines.append(draft_ticket(d))
        lines.append("```")
    return "\n".join(lines)


def draft_ticket(d):
    op, inc = d["op"], d["incident"]
    fix = d["recommendations"][0] if d["recommendations"] else {"action": "TBD", "why": ""}
    return "\n".join([
        "Title: {} slow query — {} ({})".format(op["source"], d["pattern"]["pattern"], op["shard"]),
        "",
        "Summary: {} lookup from {} filters on {}. Observed {}s.".format(
            op["collection"], op["source"], ", ".join(op["filter_fields"]) or "unknown fields", op["secs_running"]),
        "Origin: {} ({} confidence) — {}".format(d["origin"]["origin"], d["origin"]["confidence"], d["origin"]["meaning"]),
        "Deploy correlation: {} — {}".format(d["deploy"]["verdict"], d["deploy"]["note"]),
        "",
        "Evidence: {}".format(d["fanout"]["basis"]),
        "Pattern: {} ({} confidence) — {}".format(d["pattern"]["pattern"], d["pattern"]["confidence"], d["pattern"]["why"]),
        "",
        "Proposed first fix: {}".format(fix["action"]),
        "Rationale: {}".format(fix.get("why", "")),
        "",
        "Classification: {} / {}. Severity (proposed): {}{}".format(
            d["blast"]["radius"], d["blast"]["temporality"], d["severity"]["proposed"],
            " [provisional]" if d["severity"]["provisional"] else ""),
        "Kill state: kill_attempted={} kill_succeeded={}".format(op["kill_attempted"], op["kill_succeeded"]),
        "Blast radius: {} events, {} – {}".format(inc["event_count"], inc["first_seen"], inc["last_seen"]),
        "",
        "Links: Sentry {} · PagerDuty {}".format(inc.get("sentry_url") or "-", inc.get("pd_url") or "-"),
    ])


def peak_window(intervals):
    """Time range of the burst containing the peak-concurrency instant.

    Plotting the whole incident makes 70-second ops 1% of the axis, which hides the
    very overlap the chart exists to show. Zoom to the burst instead.
    """
    usable = [i for i in intervals if i[0] and i[1] and i[2]]
    if not usable:
        return None
    _count, at, _shards = peak_concurrency(usable)
    if at is None:
        return None
    live = [i for i in usable if i[0] <= at <= i[1]]
    if len(live) < 2:
        return None
    return min(i[0] for i in live), max(i[1] for i in live)


def timeline_svg(intervals, deploy_at=None, max_bars=MAX_TIMELINE_BARS, focus=None):
    """Gantt of op windows by shard. Overlapping bars on different rows ARE the fan-out proof."""
    usable = [i for i in intervals if i[0] and i[1] and i[2]]
    if not usable:
        return {"svg": '<p class="empty">No op intervals with shard attribution — timeline unavailable.</p>',
                "shown": 0, "total": 0, "focused": False, "deploy_drawn": False, "window": None}
    total = len(usable)
    if focus:
        in_focus = [i for i in usable if i[1] >= focus[0] and i[0] <= focus[1]]
        if len(in_focus) >= 2:
            usable, focused = in_focus, True
        else:
            focused = False
    else:
        focused = False
    usable.sort(key=lambda i: (i[1] - i[0]), reverse=True)
    shown = usable[:max_bars]
    shown.sort(key=lambda i: (i[2], i[0]))

    shards = sorted({i[2] for i in shown})
    row_h, pad_l, pad_t, pad_b, width = 26, 104, 16, 34, 760
    height = pad_t + row_h * len(shards) + pad_b
    t0 = min(i[0] for i in shown)
    t1 = max(i[1] for i in shown)
    span = max((t1 - t0).total_seconds(), 1.0)
    plot_w = width - pad_l - 16

    def x_of(when):
        return pad_l + (when - t0).total_seconds() / span * plot_w

    parts = ['<svg viewBox="0 0 {} {}" role="img" aria-label="Op execution windows by shard" class="tl">'.format(width, height)]
    for idx, shard in enumerate(shards):
        y = pad_t + idx * row_h
        parts.append('<line x1="{}" y1="{}" x2="{}" y2="{}" class="grid"/>'.format(pad_l, y + row_h - 1, width - 16, y + row_h - 1))
        parts.append('<text x="{}" y="{}" class="ylab">{}</text>'.format(pad_l - 10, y + 16, html.escape(shard)))
    for start, end, shard in shown:
        row = shards.index(shard)
        y = pad_t + row * row_h + 5
        x = x_of(start)
        w = max(x_of(end) - x, 3)
        secs = (end - start).total_seconds()
        parts.append(
            '<rect x="{:.1f}" y="{}" width="{:.1f}" height="14" rx="4" class="bar">'
            "<title>{} · {:.1f}s · {} → {}</title></rect>".format(
                x, y, w, html.escape(shard), secs,
                start.strftime("%H:%M:%S"), end.strftime("%H:%M:%S"))
        )
    deploy_drawn = False
    if deploy_at:
        dep = parse_ts(deploy_at)
        if dep and t0 <= dep <= t1:
            deploy_drawn = True
            dx = x_of(dep)
            parts.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" class="deploy"/>'.format(dx, pad_t - 6, dx, height - pad_b + 6))
            parts.append('<text x="{:.1f}" y="{}" class="deploylab">deploy</text>'.format(dx + 5, pad_t + 4))
    parts.append('<line x1="{}" y1="{}" x2="{}" y2="{}" class="axis"/>'.format(pad_l, height - pad_b + 6, width - 16, height - pad_b + 6))
    for frac in (0, 0.5, 1):
        when = t0 + timedelta(seconds=span * frac)
        anchor = "start" if frac == 0 else ("middle" if frac == 0.5 else "end")
        parts.append('<text x="{:.1f}" y="{}" class="xlab" text-anchor="{}">{}</text>'.format(
            pad_l + plot_w * frac, height - pad_b + 24, anchor, when.strftime("%H:%M:%S")))
    parts.append("</svg>")
    return {"svg": "".join(parts), "shown": len(shown), "total": total, "focused": focused,
            "deploy_drawn": deploy_drawn, "window": (t0, t1)}


CSS = """
:root{color-scheme:light dark}
.r{--s1:#fcfcfb;--plane:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;
--series:#2a78d6;--bd:rgba(11,11,11,.10);color-scheme:light}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])) .r{--s1:#1a1a19;--plane:#0d0d0d;--ink:#fff;
--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--series:#3987e5;--bd:rgba(255,255,255,.10);color-scheme:dark}}
:root[data-theme=dark] .r{--s1:#1a1a19;--plane:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;
--axis:#383835;--series:#3987e5;--bd:rgba(255,255,255,.10);color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);
font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:15px;margin:32px 0 10px;color:var(--ink);letter-spacing:.02em;text-transform:uppercase}
.sub{color:var(--ink2);margin:0 0 20px;font-size:13.5px}
.card{background:var(--s1);border:1px solid var(--bd);border-radius:10px;padding:16px 18px}
.banner{background:var(--s1);border:1px solid var(--bd);border-left:3px solid var(--muted);border-radius:8px;
padding:11px 14px;margin:0 0 22px;font-size:13px;color:var(--ink2)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:8px}
.tile{background:var(--s1);border:1px solid var(--bd);border-radius:10px;padding:13px 15px}
.tile .k{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.tile .v{font-size:26px;font-weight:600;margin-top:3px;line-height:1.15}
.tile .n{font-size:12px;color:var(--ink2);margin-top:2px}
.badge{display:inline-flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;
border:1px solid var(--bd);border-radius:999px;padding:3px 11px;color:var(--ink)}
.glyph{font-size:11px;line-height:1}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:6px}
th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
font-weight:600;padding:7px 9px;border-bottom:1px solid var(--axis)}
td{padding:8px 9px;border-bottom:1px solid var(--grid);vertical-align:top;color:var(--ink2)}
td:first-child,td.k{color:var(--ink);font-weight:500;white-space:nowrap}
td.num{font-variant-numeric:tabular-nums}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
code{font-size:12.5px;background:var(--plane);border:1px solid var(--bd);border-radius:4px;padding:1px 5px}
pre{background:var(--plane);border:1px solid var(--bd);border-radius:8px;padding:14px;overflow:auto;
font-size:12.5px;line-height:1.5;color:var(--ink2);white-space:pre-wrap}
.tl{width:100%;height:auto}
.tl .bar{fill:var(--series)}
.tl .grid{stroke:var(--grid);stroke-width:1}
.tl .axis{stroke:var(--axis);stroke-width:1}
.tl .deploy{stroke:var(--ink2);stroke-width:2;stroke-dasharray:none}
.tl .ylab{fill:var(--muted);font-size:11px;text-anchor:end;font-variant-numeric:tabular-nums}
.tl .xlab{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
.tl .deploylab{fill:var(--ink2);font-size:11px;font-weight:600}
.cap{color:var(--muted);font-size:12px;margin-top:8px}
.guard{border-left:3px solid #d03b3b}
.empty{color:var(--muted);font-size:13px}
.tog{position:fixed;top:14px;right:16px;background:var(--s1);color:var(--ink2);border:1px solid var(--bd);
border-radius:999px;padding:5px 13px;font:inherit;font-size:12.5px;cursor:pointer}
@media print{.tog{display:none}}
"""


def render_html(digest, mode="deep"):
    d = digest
    e = html.escape
    inc, op, sev = d["incident"], d["op"], d["severity"]
    color, glyph = SEVERITY_STYLE[sev["proposed"]]
    intervals = d.get("_intervals", [])
    tl = timeline_svg(intervals, (d["deploy"].get("nearest") or {}).get("at"), focus=peak_window(intervals))

    def row(k, v):
        return "<tr><td class='k'>{}</td><td>{}</td></tr>".format(e(k), v)

    def tile(k, v, note):
        return "<div class='tile'><div class='k'>{}</div><div class='v'>{}</div><div class='n'>{}</div></div>".format(
            e(k), v, e(note))

    src = d["meta"].get("source", "unspecified")
    banner = ""
    if src != "live":
        banner = "<div class='banner'><strong>Data source: {}.</strong> {}</div>".format(
            e(src), e(d["meta"].get("notes", "")))

    sev_badge = "<span class='badge'><span class='glyph' style='color:{}'>{}</span>{}{}</span>".format(
        color, glyph, e(sev["proposed"]), " · provisional" if sev["provisional"] else "")

    tiles = "".join([
        tile("Runtime", "{}s".format(fmt_secs(op["secs_running"])), "on {}".format(op["shard"])),
        tile("Events", "{:,}".format(inc["event_count"]) if isinstance(inc["event_count"], int) else str(inc["event_count"]),
             "{} sampled".format(inc["events_sampled"])),
        tile("Shards at once", str(d["fanout"]["peak_concurrent_shards"]),
             "{} distinct overall".format(d["fanout"]["distinct_shards"])),
        "<div class='tile'><div class='k'>Severity (proposed)</div><div class='v' style='font-size:19px;margin-top:7px'>{}</div>"
        "<div class='n'>{}</div></div>".format(sev_badge, e(d["pattern"]["pattern"])),
    ])

    evidence = "".join([
        row("Origin", "<strong>{}</strong> ({} confidence)<br><span style='color:var(--muted)'>{}</span><br><code>{}</code>".format(
            e(d["origin"]["origin"]), e(d["origin"]["confidence"]), e(d["origin"]["meaning"]),
            e("; ".join(d["origin"]["evidence"]) or "no signals"))),
        row("Deploy correlation", "<strong>{}</strong><br>{}".format(e(d["deploy"]["verdict"]), e(d["deploy"]["note"]))),
        row("Fan-out", "<strong>{}</strong><br>{}".format(e(d["fanout"]["verdict"]), e(d["fanout"]["basis"]))),
        row("Pattern", "<strong>{}</strong> ({} confidence)<br>{}".format(
            e(d["pattern"]["pattern"]), e(d["pattern"]["confidence"]), e(d["pattern"]["why"]))),
        row("Shard key", "{} <span style='color:var(--muted)'>(source: {})</span>".format(
            e(", ".join(d["shard_key"]["key"]) or "unknown"), e(d["shard_key"]["source"]))),
        row("Blast radius", "{} / {} — {} distinct account(s), {} day(s)".format(
            e(d["blast"]["radius"]), e(d["blast"]["temporality"]),
            d["blast"]["distinct_accounts"], d["blast"]["distinct_days"])),
        row("Killer", "kill_attempted={} · kill_succeeded={}".format(e(str(op["kill_attempted"])), e(str(op["kill_succeeded"])))),
        row("Plan", "<code>{}</code>".format(e(str(op["plan_summary"])))),
        row("Why this severity", e("; ".join(sev["reasons"]))),
    ])

    recs = "".join(
        "<tr><td class='num'>{}</td><td class='k'>{}</td><td style='color:var(--ink)'>{}</td><td>{}</td><td class='num'>{}</td></tr>".format(
            r["rank"], e(r["tier"]), e(r["action"]), e(r["why"]), e(r["effort"]))
        for r in d["recommendations"])

    shard_rows = "".join("<tr><td class='k'>{}</td></tr>".format(e(s)) for s in d["fanout"]["shards"])

    if tl["window"] and tl["focused"]:
        scope_note = "Zoomed to the peak-concurrency burst ({}–{} of the {}–{} incident); {} of {} attributable ops shown.".format(
            tl["window"][0].strftime("%H:%M:%S"), tl["window"][1].strftime("%H:%M:%S"),
            str(inc.get("first_seen") or "")[11:19], str(inc.get("last_seen") or "")[11:19],
            tl["shown"], tl["total"])
    else:
        scope_note = "Showing the {} longest of {} attributable ops.".format(tl["shown"], tl["total"])

    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Slow query triage — {short}</title><style>{css}</style></head>
<body class="r"><button class="tog" id="t">theme</button><div class="wrap">
<h1>Slow query triage — {short}</h1>
<p class="sub">{pdtitle} · PagerDuty {pdid} ({urgency} urgency, {service}) · window {first} – {last}</p>
{banner}
<div class="tiles">{tiles}</div>
<h2>Evidence</h2>
<div class="card"><table><tbody>{evidence}</tbody></table></div>
<h2>Shard fan-out over time</h2>
<div class="card">{svg}
<p class="cap">One bar per sampled op, positioned by start time and length (<code>secs_running</code>), grouped by shard.
Bars that overlap vertically were running <em>at the same instant on different shards</em> — that overlap is the fan-out
proof; many shards visited sequentially would not stack. {scope}{depnote}</p></div>
<h2>Recommendations</h2>
<div class="card"><table><thead><tr><th>#</th><th>Tier</th><th>Action</th><th>Why</th><th>Effort</th></tr></thead>
<tbody>{recs}</tbody></table></div>
<h2>Drafted ticket (not filed)</h2>
<div class="card"><pre>{ticket}</pre></div>
<h2>Human-only decisions</h2>
<div class="card guard"><p style="margin:0 0 8px"><strong>Kill / no-kill on a live op is a human decision.</strong>
Aborting a mid-flight write can corrupt data. This report states <code>kill_attempted={ka}</code> and
<code>kill_succeeded={ks}</code> as facts and never proposes a kill.</p>
<p style="margin:0;color:var(--ink2)">Still to confirm by hand: the shard key ({sk}), the owning team via CODEOWNERS,
and the Grafana / New Relic views for this window.</p></div>
<h2>Shards touched ({nshards})</h2>
<div class="card"><table><thead><tr><th>Shard</th></tr></thead><tbody>{shard_rows}</tbody></table></div>
</div>
<script>
var b=document.documentElement,k="sqt-theme",s=localStorage.getItem(k);if(s)b.dataset.theme=s;
document.getElementById("t").onclick=function(){{var d=b.dataset.theme==="dark"||(!b.dataset.theme&&
matchMedia("(prefers-color-scheme:dark)").matches);b.dataset.theme=d?"light":"dark";
localStorage.setItem(k,b.dataset.theme)}};
</script></body></html>""".format(
        short=e(str(inc.get("sentry_short_id") or "unknown")),
        css=CSS,
        pdtitle=e(str(inc.get("pd_title") or "Slow query")),
        pdid=e(str(inc.get("pd_id") or "-")),
        urgency=e(str(inc.get("pd_urgency") or "-")),
        service=e(str(inc.get("pd_service") or "-")),
        first=e(str(inc.get("first_seen") or "-")),
        last=e(str(inc.get("last_seen") or "-")),
        banner=banner, tiles=tiles, evidence=evidence, svg=tl["svg"],
        scope=e(scope_note), depnote=e(" A vertical marker shows the deploy that landed inside this window."
                                       if tl["deploy_drawn"] else ""),
        recs=recs, ticket=e(draft_ticket(d)),
        ka=e(str(op["kill_attempted"])), ks=e(str(op["kill_succeeded"])),
        sk=e(", ".join(d["shard_key"]["key"]) or "unknown"),
        nshards=d["fanout"]["distinct_shards"], shard_rows=shard_rows or "<tr><td>none</td></tr>",
    )


# --------------------------------------------------------------------------- fetch


def _get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_bundle(short_id, pd_incident, org="apolloio", event_limit=100):
    """Pull Sentry issue/events/deploys + the PD incident into one raw bundle.

    Uses the canonical sentry.io host; the regional subdomain is egress-denied from
    remote sessions. Credentials come from the environment or a proxy injector.
    """
    s_hdr = {"Accept": "application/json"}
    if os.environ.get("SENTRY_AUTH_TOKEN"):
        s_hdr["Authorization"] = "Bearer " + os.environ["SENTRY_AUTH_TOKEN"]
    p_hdr = {"Accept": "application/json"}
    if os.environ.get("PAGERDUTY_TOKEN"):
        p_hdr["Authorization"] = "Token token=" + os.environ["PAGERDUTY_TOKEN"]

    bundle = {"meta": {"source": "live", "fetched_at": datetime.now(timezone.utc).isoformat()}}
    short = _get("https://sentry.io/api/0/organizations/{}/shortids/{}/".format(org, short_id), s_hdr)
    group = short.get("group", {})
    bundle["sentry_issue"] = group
    issue_id = group.get("id")
    events = _get("https://sentry.io/api/0/issues/{}/events/?full=true".format(issue_id), s_hdr)
    bundle["sentry_events"] = events[:event_limit] if isinstance(events, list) else []
    release = (group.get("firstRelease") or {}).get("version")
    if release:
        try:
            bundle["deploys"] = _get(
                "https://sentry.io/api/0/organizations/{}/releases/{}/deploys/".format(org, urllib.parse.quote(release, safe="")),
                s_hdr)
        except (urllib.error.URLError, urllib.error.HTTPError):
            bundle["deploys"] = []
    if pd_incident:
        try:
            pd = _get("https://api.pagerduty.com/incidents/{}".format(pd_incident), p_hdr).get("incident", {})
            bundle["pagerduty"] = {
                "id": pd.get("id"), "incident_number": pd.get("incident_number"), "title": pd.get("title"),
                "urgency": pd.get("urgency"), "service": (pd.get("service") or {}).get("summary"),
                "created_at": pd.get("created_at"), "status": pd.get("status"), "html_url": pd.get("html_url"),
            }
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            bundle["pagerduty"] = {"id": pd_incident, "error": str(exc)}
    return bundle


# --------------------------------------------------------------------------- cli


def default_html_path(digest):
    slug = re.sub(r"[^A-Za-z0-9_-]", "", str(digest["incident"].get("sentry_short_id") or "report")) or "report"
    return os.path.join(tempfile.gettempdir(), "slow-query-{}.html".format(slug))


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Digest a Query Killer slow-query incident.")
    p.add_argument("--bundle", help="path to a raw bundle JSON (skips network)")
    p.add_argument("--fetch", action="store_true", help="fetch from Sentry/PagerDuty instead of reading a bundle")
    p.add_argument("--sentry-short-id", help="e.g. RAILS-BACKEND-4FA7")
    p.add_argument("--pd-incident", help="e.g. Q25ND367948EA8")
    p.add_argument("--org", default="apolloio")
    p.add_argument("--bundle-out", help="write the raw fetched bundle here")
    p.add_argument("--shard-key", help="comma-separated confirmed shard key, e.g. team")
    p.add_argument("--shard-key-source", help="how the shard key was confirmed (e.g. mongo-specialist)")
    p.add_argument("--mode", choices=["triage", "deep"], default="triage")
    p.add_argument("--format", choices=["md", "json", "html"], default="md")
    p.add_argument("--out", help="write output here instead of stdout")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.fetch:
        if not args.sentry_short_id:
            print("--fetch requires --sentry-short-id", file=sys.stderr)
            return 2
        try:
            bundle = fetch_bundle(args.sentry_short_id, args.pd_incident, args.org)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            print("fetch failed ({}). Sentry/PagerDuty may be egress-blocked from this "
                  "session — rerun with --bundle after fetching elsewhere.".format(exc), file=sys.stderr)
            return 3
        if args.bundle_out:
            with open(args.bundle_out, "w", encoding="utf-8") as fh:
                json.dump(bundle, fh)
    elif args.bundle:
        with open(args.bundle, encoding="utf-8") as fh:
            bundle = json.load(fh)
    else:
        print("supply --bundle FILE or --fetch", file=sys.stderr)
        return 2

    shard_key = [k.strip() for k in args.shard_key.split(",")] if args.shard_key else None
    digest = build_digest(bundle, shard_key, args.shard_key_source)

    if args.format == "json":
        payload = {k: v for k, v in digest.items() if k != "_intervals"}
        text = json.dumps(payload, indent=2, default=str)
    elif args.format == "html":
        text = render_html(digest, args.mode)
    else:
        text = render_markdown(digest, args.mode)

    # HTML always goes to a file: printing it would put ~12KB of markup into the
    # caller's context, which is the exact cost this script exists to avoid.
    out = args.out or (default_html_path(digest) if args.format == "html" else None)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote {} ({} bytes)".format(out, len(text)))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
