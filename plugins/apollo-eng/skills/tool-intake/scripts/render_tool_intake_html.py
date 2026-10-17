#!/usr/bin/env python3
"""Render a redacted tool-intake JSON report as standalone HTML."""

from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_TOP_LEVEL = {"tool", "approval", "verdict"}
UNKNOWN_APPROVAL_STATES = {"NO_MATCH_REVIEW_REQUIRED", "STALE_RECONFIRM"}
VALID_APPROVAL_STATES = {
    "APPROVED",
    "APPROVED_WITH_CONDITIONS",
    "RESTRICTED_OR_DENIED",
    "STALE_RECONFIRM",
    "NO_MATCH_REVIEW_REQUIRED",
}
ZIP_GUIDE_URL = "https://www.notion.so/2feab2b3b49680ee9309d07a5fc58111"
PROCUREMENT_FAQ_URL = "https://www.notion.so/176ab2b3b49680f991e4f051934f41e6"
ZIP_REQUEST_URL = "https://apollo.zip.com/create-workflow-request"
ZIP_HELP_URL = "https://apolloio.slack.com/archives/C078HCHU1SL"
GUIDANCE_PREFIXES = ("collect ", "confirm ", "define ", "document ", "obtain ", "list ", "map ", "require ", "review ", "tbd")


def safe_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def text(value: object, fallback: str = "Not provided") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def validate_report(report: object) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    missing = REQUIRED_TOP_LEVEL - report.keys()
    if missing:
        raise ValueError(f"report is missing: {', '.join(sorted(missing))}")
    for key in REQUIRED_TOP_LEVEL:
        if not isinstance(report[key], dict):
            raise ValueError(f"{key} must be an object")
    primary_classification = report["tool"].get("primary_classification")
    if not isinstance(primary_classification, str) or not primary_classification.strip():
        raise ValueError("tool.primary_classification is required")
    approval_status = report["approval"].get("status")
    if not isinstance(approval_status, str) or approval_status not in VALID_APPROVAL_STATES:
        raise ValueError("approval.status must use a supported user-facing approval state")
    if approval_status in UNKNOWN_APPROVAL_STATES:
        safe_test = report.get("safe_test")
        if not isinstance(safe_test, list) or not safe_test:
            raise ValueError("unknown-tool reports must include a non-empty safe_test plan")
    return report


def render_items(items: object, empty: str = "No items recorded.") -> str:
    if not isinstance(items, list) or not items:
        return f'<p class="empty">{html.escape(empty)}</p>'
    rendered = []
    for item in items:
        if isinstance(item, dict):
            label = text(item.get("label") or item.get("confidence"), "")
            claim = text(item.get("claim") or item.get("text") or item.get("relevance") or item.get("name") or item.get("title"))
            source = safe_url(item.get("source_url") or item.get("url"))
            prefix = f'<span class="evidence-label">{html.escape(label)}</span> ' if label else ""
            suffix = (
                f' <a href="{html.escape(source, quote=True)}" target="_blank" rel="noopener noreferrer">source</a>'
                if source
                else ""
            )
            rendered.append(f"<li>{prefix}{html.escape(claim)}{suffix}</li>")
        else:
            rendered.append(f"<li>{html.escape(text(item))}</li>")
    return "<ul>" + "".join(rendered) + "</ul>"


def render_sources(items: object) -> str:
    if not isinstance(items, list) or not items:
        return '<p class="empty">No public source links recorded.</p>'
    rendered = []
    for item in items:
        if isinstance(item, dict):
            url = safe_url(item.get("url"))
            label = text(item.get("title") or item.get("label") or url, "Source")
        else:
            url = safe_url(item)
            label = text(url, "Source")
        if url:
            rendered.append(
                f'<li><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a></li>'
            )
        else:
            rendered.append(f'<li>{html.escape(label)} <span class="gap">invalid or private URL omitted</span></li>')
    return "<ul>" + "".join(rendered) + "</ul>"


def render_related(items: object) -> str:
    if not isinstance(items, list) or not items:
        return '<span class="muted">None</span>'
    rendered = []
    for item in items:
        if isinstance(item, dict):
            name = html.escape(text(item.get("name"), "Related component"))
            role = html.escape(text(item.get("role"), ""))
            url = safe_url(item.get("url"))
            label = f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{name}</a>' if url else name
            rendered.append(f'<span class="component">{label}{f" · {role}" if role else ""}</span>')
        else:
            rendered.append(f'<span class="component">{html.escape(text(item))}</span>')
    return "".join(rendered)


def render_primary_links(tool: dict[str, Any], company: dict[str, Any]) -> str:
    links = []
    homepage = safe_url(tool.get("homepage_url") or company.get("website"))
    pricing = safe_url(company.get("pricing_url"))
    if homepage:
        links.append(
            f'<a class="primary-link" href="{html.escape(homepage, quote=True)}" target="_blank" rel="noopener noreferrer">Product site <span>↗</span></a>'
        )
    if pricing:
        links.append(
            f'<a class="primary-link pricing" href="{html.escape(pricing, quote=True)}" target="_blank" rel="noopener noreferrer">Pricing <span>↗</span></a>'
        )
    return '<div class="primary-links">' + "".join(links) + "</div>" if links else ""


def render_approval_links(approval: dict[str, Any]) -> str:
    links = []
    fields = [
        ("channel_url", "Slack channel"),
        ("apps_db_url", "Apps DB"),
        ("initial_request_url", "Initial request"),
        ("source_url", "Approval source"),
    ]
    seen_urls = set()
    for field, label in fields:
        url = safe_url(approval.get(field))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        links.append(
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)} ↗</a>'
        )
    owner = text(approval.get("owner"), "")
    owner_html = f'<span><b>Owner:</b> {html.escape(owner)}</span>' if owner else ""
    if not links and not owner_html:
        return ""
    return '<div class="approval-meta">' + owner_html + "".join(links) + "</div>"


def metric(label: str, value: object, url: object = None) -> str:
    if value is None or value == "":
        return ""
    rendered_value = html.escape(text(value))
    link = safe_url(url)
    if link:
        rendered_value = f'<a href="{html.escape(link, quote=True)}" target="_blank" rel="noopener noreferrer">{rendered_value}</a>'
    return f'<div class="metric"><span>{html.escape(label)}</span><strong>{rendered_value}</strong></div>'


def render_profile(report: dict[str, Any]) -> str:
    company = report.get("company") if isinstance(report.get("company"), dict) else {}
    oss = report.get("open_source") if isinstance(report.get("open_source"), dict) else {}
    tool = report.get("tool") if isinstance(report.get("tool"), dict) else {}
    primary_classification = text(tool.get("primary_classification"), "").casefold()
    cards = []
    if oss and primary_classification != "saas":
        stars = oss.get("stars")
        if isinstance(stars, int):
            stars = f"{stars:,}"
        cards.extend([
            metric("GitHub stars", stars, oss.get("repository_url")),
            metric("License", oss.get("license")),
            metric("Latest release", oss.get("latest_release"), oss.get("release_url")),
            metric("Maintainer", oss.get("maintainer")),
        ])
    if company:
        cards.extend([
            metric("Company", company.get("name"), company.get("website")),
            metric("Founded", company.get("founded")),
            metric("Location", company.get("headquarters")),
            metric("Funding / ownership", company.get("funding_or_ownership"), company.get("funding_source_url")),
        ])
    cards = [card for card in cards if card]
    if not cards:
        return '<p class="empty">No maturity or company details recorded.</p>'
    return '<div class="metrics">' + "".join(cards) + "</div>"


def render_market(market: object) -> str:
    competitors = market.get("competitors") if isinstance(market, dict) else None
    if not isinstance(competitors, list) or not competitors:
        return '<p class="empty">No useful comparable products recorded.</p>'
    cards = []
    for item in competitors[:2]:
        if not isinstance(item, dict):
            continue
        name = html.escape(text(item.get("name"), "Comparable product"))
        why = html.escape(text(item.get("why"), ""))
        url = safe_url(item.get("url"))
        name_html = f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{name}</a>' if url else name
        cards.append(f'<article class="compare"><strong>{name_html}</strong><p>{why}</p></article>')
    return '<div class="compare-grid">' + "".join(cards) + "</div>" if cards else '<p class="empty">No useful comparable products recorded.</p>'


def render_intake(packet: object) -> str:
    packet = packet if isinstance(packet, dict) else {}
    omitted_fields = set(packet.get("omit_fields", [])) if isinstance(packet.get("omit_fields"), list) else set()
    fields = [
        ("business_problem", "Business problem and intended use"),
        ("business_owner", "Business owner"),
        ("intended_users", "Users and expected scale"),
        ("data_and_classification", "Data involved and classification"),
        ("permissions_and_integrations", "Permissions and integrations"),
        ("egress_and_subprocessors", "Network destinations and subprocessors"),
        ("retention_training_and_deletion", "Retention, AI training, and deletion"),
        ("terms_and_pricing", "Terms, DPA, and expected cost"),
        ("alternatives_considered", "Apollo alternatives considered"),
        ("test_scope", "Isolated test scope and cleanup"),
    ]
    rows = []
    for key, label in fields:
        if key in omitted_fields:
            continue
        value = packet.get(key)
        needs_collection = not value or text(value).strip().casefold().startswith(GUIDANCE_PREFIXES)
        if value and not needs_collection:
            rows.append(f'<li class="ready"><span>Ready</span><strong>{html.escape(label)}</strong><p>{html.escape(text(value))}</p></li>')
        else:
            guidance = f'<p>{html.escape(text(value))}</p>' if value else ""
            rows.append(f'<li class="needed"><span>Collect</span><strong>{html.escape(label)}</strong>{guidance}</li>')
    supplied_links = packet.get("links") if isinstance(packet.get("links"), list) else []
    required_links = [
        {"title": "Start a Zip request", "url": ZIP_REQUEST_URL},
        {"title": "Zip Guide", "url": ZIP_GUIDE_URL},
        {"title": "Procurement FAQ", "url": PROCUREMENT_FAQ_URL},
        {"title": "#zip-help-desk", "url": ZIP_HELP_URL},
    ]
    links = []
    seen_urls = set()
    for item in [*supplied_links, *required_links]:
        url = safe_url(item.get("url")) if isinstance(item, dict) else safe_url(item)
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        links.append(item)
    return '<div class="intake-layout"><ol class="checklist">' + "".join(rows) + f'</ol><aside><h3>Start here</h3>{render_sources(links)}<p>Use #zip-help-desk if the correct workflow is unclear.</p></aside></div>'


def logo_data_uri(asset_path: Path | None) -> str | None:
    if not asset_path or not asset_path.is_file():
        return None
    return "data:image/png;base64," + base64.b64encode(asset_path.read_bytes()).decode("ascii")


def render_report(report: dict[str, Any], logo: str | None = None) -> str:
    report = validate_report(report)
    tool = report["tool"]
    approval = report["approval"]
    verdict = report["verdict"]
    status = text(approval.get("status"), "NO_MATCH_REVIEW_REQUIRED")
    status_class = {
        "APPROVED": "positive",
        "APPROVED_WITH_CONDITIONS": "caution",
        "RESTRICTED_OR_DENIED": "danger",
        "STALE_RECONFIRM": "stale",
        "NO_MATCH_REVIEW_REQUIRED": "neutral",
    }[status]
    status_label = {
        "APPROVED": "Approved",
        "APPROVED_WITH_CONDITIONS": "Approved with conditions",
        "RESTRICTED_OR_DENIED": "Restricted or denied",
        "STALE_RECONFIRM": "Reconfirm approval",
        "NO_MATCH_REVIEW_REQUIRED": "Approval not verified",
    }.get(status, status.replace("_", " ").title())
    action = text(verdict.get("action"))
    action_label = action.replace("_", " ").title()
    action_url = safe_url(verdict.get("action_url"))
    if not action_url and action == "PREPARE_ZIP_INTAKE":
        action_url = ZIP_REQUEST_URL
    action_html = (
        f'<a href="{html.escape(action_url, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(action_label)}</a>'
        if action_url else html.escape(action_label)
    )
    logo_html = f'<img src="{html.escape(logo, quote=True)}" alt="">' if logo else '<span class="logo-fallback">A</span>'
    tool_logo_url = safe_url(tool.get("logo_url"))
    tool_logo = (
        f'<img class="tool-logo" src="{html.escape(tool_logo_url, quote=True)}" alt="{html.escape(text(tool.get("name")), quote=True)} logo">'
        if tool_logo_url else f'<span class="tool-logo fallback">{html.escape(text(tool.get("name"), "T")[:1].upper())}</span>'
    )
    classification = text(tool.get("primary_classification"))
    title = text(tool.get("name"), "Tool intake")
    company = report.get("company") if isinstance(report.get("company"), dict) else {}
    pricing_summary = text(company.get("pricing_summary"), "")
    pricing_tldr = (
        f'<div class="pricing-tldr"><span>Pricing TL;DR</span><strong>{html.escape(pricing_summary)}</strong></div>'
        if pricing_summary
        else ""
    )
    primary_links = render_primary_links(tool, company)
    approval_links = render_approval_links(approval)
    process_heading = "Use and change controls" if status in {"APPROVED", "APPROVED_WITH_CONDITIONS"} else "Zip-ready intake packet"

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Apollo Tool Intake</title>
<style>
:root{{--ink:#252521;--muted:#66665f;--paper:#f3f1eb;--white:#fff;--line:#d8d4c9;--sun:#f8ff2c;--sun-soft:#fbffd4;--purple:#7067f0;--warn:#fff0b8;--danger:#ffd8d2;--stale:#e7e3ff;--good:#dff5d2;--blue:#e8efff}}*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#f8f6ef 0,#efede6 100%);color:var(--ink);font:15px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}}a{{color:inherit;text-decoration-thickness:1px;text-underline-offset:3px}}header{{align-items:center;background:var(--ink);color:white;display:flex;gap:12px;padding:12px max(24px,calc((100vw - 1120px)/2))}}header img,.logo-fallback{{background:var(--sun);border-radius:8px;height:30px;object-fit:contain;padding:5px;width:30px}}header strong{{letter-spacing:.02em}}main{{margin:auto;max-width:1120px;padding:20px 24px 42px}}.hero{{background:linear-gradient(120deg,var(--white) 0,var(--sun-soft) 100%);border:1px solid var(--line);border-radius:22px;box-shadow:0 14px 40px rgba(37,37,33,.07);overflow:hidden;padding:24px;position:relative}}.hero-top{{align-items:flex-start;display:flex;gap:18px}}.tool-logo{{background:white;border:1px solid var(--line);border-radius:16px;height:70px;object-fit:contain;padding:8px;width:70px}}.tool-logo.fallback{{align-items:center;background:var(--ink);color:var(--sun);display:flex;font-size:30px;font-weight:850;justify-content:center}}.eyebrow,.kicker{{font-size:11px;font-weight:850;letter-spacing:.13em;text-transform:uppercase}}h1{{font-size:clamp(32px,5vw,54px);letter-spacing:-.045em;line-height:1.02;margin:6px 0 10px}}h2{{font-size:20px;letter-spacing:-.015em;margin:0 0 10px}}h3{{font-size:14px;margin:0 0 8px}}p{{margin:6px 0}}.summary{{font-size:18px;max-width:820px}}.primary-links{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}.primary-link{{background:var(--ink);border-radius:10px;color:white;font-size:13px;font-weight:800;padding:9px 12px;text-decoration:none}}.primary-link.pricing{{background:var(--purple)}}.pricing-tldr{{background:var(--sun);border-radius:11px;margin-top:10px;max-width:720px;padding:10px 12px}}.pricing-tldr span{{display:block;font-size:10px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}.decision{{display:grid;gap:10px;grid-template-columns:1.1fr 1fr .65fr;margin-top:16px}}.decision>div{{background:rgba(255,255,255,.74);border:1px solid rgba(37,37,33,.08);border-radius:13px;padding:13px}}.decision span,.metric span{{color:var(--muted);display:block;font-size:10px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}.components{{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}}.component{{background:var(--blue);border-radius:999px;font-size:11px;padding:4px 8px}}.status{{border-radius:999px;display:inline-block;font-size:12px;font-weight:850;margin-top:8px;padding:6px 11px}}.status.positive{{background:var(--good)}}.status.caution{{background:var(--warn)}}.status.danger{{background:var(--danger);color:#8a1f17}}.status.stale{{background:var(--stale);color:#4131a3}}.status.neutral{{background:var(--sun)}}.grid{{display:grid;gap:10px;grid-template-columns:repeat(12,minmax(0,1fr));margin-top:10px}}section{{background:var(--white);border:1px solid var(--line);border-radius:16px;grid-column:span 6;padding:16px}}section.wide{{grid-column:1/-1}}section.profile{{background:var(--ink);color:white}}section.profile .muted,section.profile .metric span{{color:#c9c8c2}}.metrics{{display:grid;gap:8px;grid-template-columns:repeat(4,minmax(0,1fr))}}.metric{{background:rgba(255,255,255,.1);border-radius:11px;min-height:68px;padding:11px}}.metric strong{{display:block;font-size:14px;margin-top:5px;overflow-wrap:anywhere}}.approval-meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}.approval-meta a,.approval-meta span{{background:var(--paper);border-radius:8px;font-size:12px;padding:7px 9px}}details{{background:var(--white);border:1px solid var(--line);border-radius:16px;grid-column:1/-1;overflow:hidden}}summary{{align-items:center;cursor:pointer;display:flex;font-size:18px;font-weight:850;justify-content:space-between;list-style:none;padding:15px 18px}}summary::-webkit-details-marker{{display:none}}summary::after{{content:'+';font-size:23px;font-weight:500}}details[open] summary::after{{content:'−'}}details[open] summary{{border-bottom:1px solid var(--line)}}.detail-grid{{display:grid;gap:1px;grid-template-columns:repeat(2,1fr);background:var(--line)}}.detail-grid section{{border:0;border-radius:0;grid-column:auto}}.detail-grid section.wide{{grid-column:1/-1}}ul{{margin:7px 0 0;padding-left:20px}}li+li{{margin-top:6px}}.empty,.gap,.muted{{color:var(--muted)}}.evidence-label{{font-size:10px;font-weight:850;letter-spacing:.05em}}.compare-grid{{display:grid;gap:8px;grid-template-columns:repeat(2,1fr)}}.compare{{background:var(--paper);border-radius:11px;padding:12px}}.compare p{{color:var(--muted);font-size:13px}}.intake-layout{{display:grid;gap:18px;grid-template-columns:2fr 1fr}}.checklist{{display:grid;gap:7px;grid-template-columns:repeat(2,1fr);list-style:none;margin:0;padding:0}}.checklist li{{background:var(--paper);border-radius:10px;margin:0;padding:10px}}.checklist li span{{background:var(--sun);border-radius:999px;display:inline-block;font-size:9px;font-weight:850;margin-right:6px;padding:3px 6px;text-transform:uppercase}}.checklist li.ready span{{background:var(--good)}}.checklist li p{{color:var(--muted);font-size:12px}}aside{{background:var(--sun-soft);border-radius:12px;padding:14px}}footer{{color:var(--muted);font-size:12px;margin-top:16px}}@media(max-width:760px){{.decision,.metrics,.intake-layout,.checklist,.detail-grid{{grid-template-columns:1fr}}section{{grid-column:1/-1}}.detail-grid section.wide{{grid-column:1}}.hero-top{{align-items:center}}.tool-logo{{height:54px;width:54px}}}}
</style></head><body>
<header>{logo_html}<strong>Apollo Tool Intake</strong></header>
	<main><article class="hero"><div class="hero-top">{tool_logo}<div><div class="eyebrow">Tool intake</div><h1>{html.escape(title)}</h1>
	<p class="summary">{html.escape(text(verdict.get("summary")))}</p><span class="status {status_class}">{html.escape(status_label)}</span>{primary_links}{pricing_tldr}</div></div>
	<div class="decision"><div><span>Primary type</span><strong>{html.escape(classification)}</strong><div class="components">{render_related(tool.get("related_components"))}</div></div><div><span>Recommended path</span><strong>{action_html}</strong></div><div><span>Version</span><strong>{html.escape(text(tool.get("version"), "Unknown"))}</strong></div></div></article>
	<div class="grid">
	<section class="wide profile"><div class="kicker">Project or company</div><h2>Maturity snapshot</h2>{render_profile(report)}</section>
	<section><div class="kicker">Approval evidence</div><h2>{html.escape(text(approval.get("summary")))}</h2><p>Scope: {html.escape(text(approval.get("scope")))}</p><p>Snapshot: {html.escape(text(approval.get("snapshot_version")))}</p>{approval_links}</section>
	<details open><summary>Evidence and risk</summary><div class="detail-grid">
<section><div class="kicker">Evidence</div><h2>What is verified</h2>{render_items(report.get("evidence"))}</section>
	<section><div class="kicker">Risk review</div><h2>Sharp edges</h2>{render_items(report.get("risks"))}</section>
	<section><div class="kicker">Apollo policy</div><h2>What applies</h2>{render_items(report.get("policies"), "No directly related Apollo policy recorded.")}</section>
	<section><div class="kicker">Customer trust</div><h2>Brand and jurisdiction</h2>{render_items(report.get("brand_risks"), "No specific brand or jurisdiction risk surfaced.")}</section>
<section class="wide"><div class="kicker">Evidence gaps</div><h2>What remains unknown</h2>{render_items(report.get("gaps"))}</section>
	</div></details>
	<details><summary>Apollo fit and alternatives</summary><div class="detail-grid">
	<section><div class="kicker">Apollo fit</div><h2>Existing options</h2>{render_items(report.get("apollo_alternatives"))}</section>
	<section><div class="kicker">Internal trail</div><h2>Related requests</h2>{render_items(report.get("related_requests"), "No matching Slack request was verified.")}</section>
	<section class="wide"><div class="kicker">Market context</div><h2>Comparable products</h2>{render_market(report.get("market"))}</section>
	</div></details>
	<details><summary>Test and intake</summary><div class="detail-grid">
<section class="wide"><div class="kicker">Low-risk path</div><h2>Proposed test controls</h2>{render_items(report.get("safe_test"))}</section>
<section class="wide"><div class="kicker">Process handoff</div><h2>{process_heading}</h2>{render_intake(report.get("intake_packet"))}</section>
<section class="wide"><div class="kicker">Sources</div><h2>Evidence reviewed</h2>{render_sources(report.get("sources"))}</section>
	</div></details>
	</div><footer>Generated {html.escape(text(report.get("generated_at")))} from the linked evidence. Verified facts, inferences, and gaps are labeled separately.</footer></main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--logo", type=Path)
    args = parser.parse_args()

    report = validate_report(json.loads(args.input.read_text(encoding="utf-8")))
    default_logo = Path(__file__).resolve().parent.parent / "assets" / "apollo-icon-stone.png"
    logo = logo_data_uri(args.logo or default_logo)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(report, logo), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
