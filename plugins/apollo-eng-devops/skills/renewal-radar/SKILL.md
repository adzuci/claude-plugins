---
name: renewal-radar
description: Manual-invocation only. Pull a team's upcoming vendor renewals live from Zip. Run via /apollo-eng-devops:renewal-radar.
argument-hint: '[TEAM] [--days N] [--status LIST] [--contractors all|exclude|only] [--html]'
disable-model-invocation: true
---

# Renewal Radar

**Invoke directly.** Run this skill as `/apollo-eng-devops:renewal-radar [TEAM] [flags]`. It lives in the `apollo-eng-devops` plugin because DevOps/Infrastructure is its default and primary user, but it takes any team/department as an argument — see [Arguments](#arguments).

`disable-model-invocation: true` is intentional and should stay. "Renewal", "contract", "vendor", and "Zip" language would otherwise collide with [`apollo-procurement:procurement-faq`](../../../apollo-procurement/skills/procurement-faq/SKILL.md), which is model-invocable and already claims contract renewals, and with [`apollo-legal:vendor-negotiation-support`](../../../apollo-legal/skills/vendor-negotiation-support/SKILL.md). This skill is direct-invoke only so it never steals routing from either.

Use this skill to produce a live, read-only digest of a team's upcoming vendor renewals straight from Zip, bucketed by urgency, so a renewal does not land as a surprise.

Audience: Apollo engineers and engineering managers who own vendor spend for a team.

<!-- Maintainer note: this skill is deliberately SKILL.md + references/ only. No scripts/, no tests/.
     Unlike check-uptime, which owns an HTTP client, auth, and retry surface worth unit-testing,
     every byte of data here arrives through Zip MCP tool calls that only the model can make.
     A Python script would have no data source of its own and would just double-marshal the same
     fat JSON records through context for no benefit. See check-apdex and check-cloudflare in this
     plugin for the same-plugin precedent for a SKILL.md + references/-only skill. -->

## Arguments

All arguments are optional. With no arguments, report the next 120 days of `UPCOMING` and `NOT_SCHEDULED` renewals for the `Infrastructure` department (DevOps's own default).

```text
/apollo-eng-devops:renewal-radar [TEAM] [--team NAME] [--days N] [--end-before YYYY-MM-DD] [--status LIST] [--all-open] [--min-amount N] [--mine] [--no-vendor-sweep] [--contractors all|exclude|only] [--html]
```

| Argument | Default | Meaning |
|---|---|---|
| `TEAM` (positional) | `Infrastructure` | Free-text team/department name, or a raw `department_guid` (detect by UUID shape) |
| `--team NAME` | — | Same as the positional `TEAM`, for callers who prefer an explicit flag (e.g. scripting, or when other flags come first). If both the positional and `--team` are given, they must agree — if they don't, ask which one the user meant rather than picking one. |
| `--days N` | `120` | Lookahead window, so `end_date_before = today + N days` |
| `--end-before YYYY-MM-DD` | none | Explicit window end. Mutually exclusive with `--days` |
| `--status LIST` | `UPCOMING,NOT_SCHEDULED` | Comma-separated `renewal_status` enum names |
| `--all-open` | off | Shorthand that adds `RENEWAL_IN_PROGRESS,CANCELLATION_IN_PROGRESS` to the status set |
| `--min-amount N` | none | Dollars, converted to `total_cents_min = N * 100` |
| `--mine` | off | Adds `creator_guid` from `whoami`, narrowing to contracts the caller filed |
| `--no-vendor-sweep` | off | Skip the vendor sweep (step 3) |
| `--contractors all\|exclude\|only` | `all` | Filter individual-contractor engagements (see below). `all` changes nothing; `exclude` drops them (e.g. to skip a person like Marcelo and see only tooling/vendor renewals); `only` shows just them |
| `--html` | off | Also write a static HTML report to disk in addition to the terminal digest (step 6) |

If both `--days` and `--end-before` are given, ask which one the user meant rather than silently picking one.

### Contractors vs. vendors (`--contractors`)

Zip has one taxonomy for both: an individual contractor engagement (a person, paid for their time, e.g. "Marcelo Teixeira de Mendonca Tecnologia ME") and a software/tooling vendor (a company, paid for a product) both come back as `ZContract` hits from the same `list_agreements` call, with no boolean field distinguishing them. The reliable signal is Apollo's own Zip taxonomy, confirmed against real requests: category `Consulting, Staffing, and Professional Services` with subcategory `Request an Individual Contractor`. Detect a contractor hit by a case-insensitive match on `Individual Contractor` in the hit's subcategory name (fall back to the category name matching `Consulting, Staffing, and Professional Services` if subcategory is absent). This is a heuristic on Apollo's actual, consistently-used taxonomy, not a guess — but a hit that doesn't fit the pattern (e.g. a staffing agency contract that isn't an individual) should stay in the default `all` bucket rather than being force-classified.

- `all` (default): no filtering, unchanged from today's behavior.
- `exclude`: drop contractor hits from every bucket, but say how many were dropped and name them in one line (e.g. "Excluded 1 contractor engagement: Marcelo Teixeira de Mendonca Tecnologia ME (#640)") — never drop rows silently.
- `only`: keep just the contractor hits; useful for an EM who specifically wants to see contractor-renewal timing (e.g. before a headcount planning conversation), separate from tooling spend.

### Why 120 days

IronClad's built-in renewal alerting fires at 90 days and only for contracts above $50K. This skill is deliberately wider and has no amount floor, because it is an earlier-warning layer, not a replacement. A 120-day default gives a full quarter of runway to decide, negotiate, or cancel before the 90-day alert would even fire.

### Why `NOT_SCHEDULED` is in the default status set

`NOT_SCHEDULED` means the contract has no renewal alert configured at all. Those are the highest-risk and easiest-to-miss agreements in Zip, precisely because nothing else will ever remind anyone about them. Leaving them out would hide the exact set this skill exists to surface.

## "Team" Means Department

In Zip, a team is a **department**: an ERP/NetSuite cost-center path such as `Research and Development : Engineering : Infrastructure`. It is **not** a Slack channel, a Jira project, or a reporting line.

A contract can be filed under a parent or sibling department rather than the requester's own team. A contract owned by a DevOps engineer may sit under `Research and Development : Engineering : Engineering Leadership`. Treat department as a strong hint, never as ground truth, and say so in the output.

## Zip Access Is Permission-Gated, Not Slack-Gated

Being in `#zip-help-desk` does **not** grant Zip data access. That channel is Tyler Davis's team's employee-facing support channel for Zip questions — anyone can join it, and joining it changes nothing about what this skill can read. What actually gates `list_departments` and broad `list_agreements` reads is the caller's **Zip permission group**, assigned by Procurement. `#zip-help-desk` is where you *ask* for that grant, not where you get it by being a member. See [`references/zip-mcp-setup.md`](references/zip-mcp-setup.md) for the exact error text and the escalation path.

## Workflow

### 1. Preflight

Call `whoami` and print exactly one line before anything else:

```text
Tools: Zip MCP [ok/missing]   Scope: <email> (org <organization_guid>)
```

`whoami` only returns `user_guid`, `email`, and `organization_guid` — it cannot tell you whether department read is allowed. Do not claim a department-read status here; that is only known once step 2 attempts `list_departments`.

If the `zip` MCP tool namespace is not available at all, **stop**. Point the user at [`references/zip-mcp-setup.md`](references/zip-mcp-setup.md). Do not guess, do not reconstruct a digest from memory, and do not fabricate rows.

### 2. Resolve the team to a department

First, resolve `TEAM` to a department. Follow this ladder in order and stop at the first success:

1. **GUID passthrough.** If `TEAM` matches a UUID shape, use it directly as `department_guid`. The display name is unknown until the first hit returns one; echo the GUID until then.

1. **`list_departments(name=<TEAM>)`** — case-insensitive substring match. Once this call is attempted, report the result as part of the resolution echo: `Department read: ok` (it returned normally) or `Department read: denied` (it errored on permissions — see the fallback below).

   - Exactly 1 match: use it and echo the full department path name.
   - 2 or more matches: **stop and ask.** Print a numbered list of the full department paths and have the user pick. Never auto-select the "closest" or the shortest name.
   - 0 matches: say so explicitly, leave `department_guid` unresolved, and skip the primary step 4 query. The step 3 vendor sweep (below) still runs and is the only signal available in this case, so use its filtered results as the working set rather than treating a zero-match as "return an empty digest." If `--no-vendor-sweep` was also passed, return an empty digest with a clear note that no department could be resolved and no query was run.

1. **Permission-denied fallback.** If `list_departments` errors with a permission or access message, do **not** fail. Print a one-line notice:

   ```text
   Department read unavailable for this token — falling back to unfiltered query with client-side matching.
   ```

   Then call `list_agreements` **without** `department_guid` and match `TEAM` as a case-insensitive substring against each hit's `department.name` client-side. Present two buckets:

   - rows whose department matched `TEAM` — this is the actual digest, and
   - separately, visibly, and clearly labeled as **not confirmed to belong to `TEAM`**, rows in **other** departments.

   The second bucket exists only so a contract mis-filed under a sibling department doesn't silently vanish — it is a diagnostic, not part of the requested team's renewal set. Never present it under the same heading or table as the matched rows, and never fold its totals into any "team spend" summary. Apply the same page and row caps from step 4 to this path so it cannot run away if permissions are later widened.

Always echo the resolved department (GUID plus full path name), the zero-match notice, or the permission-denied fallback notice before moving to step 3.

### 3. Vendor sweep (always, unless `--no-vendor-sweep`)

Independent of how step 2 resolved — GUID, exact department match, zero matches, or the permission-denied fallback — run the vendor sweep unless `--no-vendor-sweep` was passed. This is not a fallback branch of the ladder; it is a standing cross-check that recovers real renewal rows the step 4 query missed, not just a "no visible contract" note.

Look up the resolved team's section in [`references/team-vendor-lists.md`](references/team-vendor-lists.md) (e.g. "DevOps / Infrastructure"). If that team has no section yet, say so and skip the sweep rather than borrowing another team's list. Otherwise, for each vendor in that section:

1. `list_vendors(name=<vendor>)`. Zero hits: report "no Zip vendor record" (see `references/team-vendor-lists.md` for what that usually means) and move on.

1. For each vendor GUID found, `list_agreements(vendor_guid=<guid>)` with **no other server-side filters**. This is the important part: Zip's per-row visibility differs by which filter you use, and `vendor_guid` alone can surface agreements the step 4 query's department/creator scoping hid entirely — confirmed live (Cloudflare and Grafana agreements were invisible to an unfiltered/department query but visible by vendor GUID).

   Before keeping a hit, reapply every requested non-department filter client-side: `agreement_status`, `renewal_status`, the inclusive end-date window, `total_cents_min`, and `creator_guid` under `--mine`. Drop hits that fail any filter; never let the visibility workaround add expired, inactive, out-of-window, wrong-status, under-threshold, or wrong-creator rows. Department scope is the one intentional exception because the sweep exists to recover tracked vendors filed under a parent or sibling department. Retain the hit's department name so that broader scope stays visible.

   Hold the filtered hits for the working set. After step 4, merge hits not already returned by the primary query (dedupe by agreement `guid`) and tag them so the digest can mark them distinctly (see step 5's formatting rules). When step 4 is skipped after zero department matches, these filtered sweep hits are the entire working set.

1. If step 3.2 returns nothing but `list_purchase_orders(vendor_guid=<guid>)` shows a PO referencing a non-null `agreement_number`, try `list_agreements(agreement_number_str=<that number>)` once. If that also returns nothing, the formal agreement is invisible to this token by any filter tried — report the PO(s) directly instead (po_number, amount, end_date_str) with an explicit note that the underlying Agreement record could not be resolved.

   If more than one PO exists for the vendor, always list all of them (never silently drop one), but rank which is most likely the **live** renewal using two Zip-native signals, in this order:

   - `total_open_amount_str == "0"` (fully billed out) is a strong signal that PO is a **closed-out prior term**, not the current one — a live renewal almost always still has an open balance.
   - Among the remaining candidates, prefer the one whose `start_date_str` is closest to today (including a start date in the past, which is normal for an already-in-progress term) over one that starts further out or has already fully lapsed.

   State the ranked pick plus the reasoning in one line (e.g. "#1540 looks live: open balance $382,220.41, started 2026-07-01; #90 looks closed out: $0 open, though its own end_date_str hasn't passed"), and still show the other PO(s) underneath rather than hiding them. Do not stop at "can't tell which" when this signal resolves it — that undersells information Zip already returns. A vendor whose renewal was signed early relative to the prior term's own end date is a normal case (see `references/team-vendor-lists.md`'s note on Redpanda), not a sign of a data error — one line item reading as a true-up or correction is often just a proration adjustment from that early switch-over, not evidence the PO isn't a real term.

1. If a vendor has a Zip vendor record but no agreement or usable PO was found by any of the above, report "Zip has this vendor, no visible contract" as before. Silence is not an acceptable answer at any point in this sweep.

### 4. Query agreements

Full parameter documentation lives in [`references/zip-agreements.md`](references/zip-agreements.md). The primary call:

If step 2 returned zero department matches, skip this call entirely; there is no valid `department_guid` to send and an unfiltered query is not authorized by that branch. Continue with the filtered vendor-sweep working set from step 3 (or an explicitly empty set when `--no-vendor-sweep` was passed).

```text
list_agreements(
  department_guid = <resolved, or omitted only under the permission-denied fallback>,
  renewal_status  = ["UPCOMING", "NOT_SCHEDULED"],   # or from --status / --all-open
  agreement_status= ["ACTIVE"],
  end_date_before = <today + N days>,
  end_date_after  = <today>,          # drops already-expired agreements
  total_cents_min = <--min-amount * 100, if given>,
  creator_guid    = <whoami().user_guid, if --mine>,
  sort_by         = "end_date_or_max_date",
  sort_order      = "asc",
  page_size       = 25
)
```

`end_date_after = today` intentionally drops expired agreements. If a user asks for expired ones, that would be an `--include-expired` flag; it is not implemented today, so say so rather than improvising.

**Pagination.** Loop while `cursor` is non-null, passing it back on each call. Keep `page_size` at 25, not 100: each hit is a fat nested `ZContract` of roughly 2KB, and 100 per page risks blowing context. Hard-cap the loop at **8 pages or 200 rows**, whichever comes first. If `total` exceeds what was shown, say `showing N of <total>` explicitly and suggest narrowing with `--days` or `--min-amount`.

**Field extraction.** Pull only these fields from each hit and discard the rest. Attachments, categories, subcategories, requests, purchase-order bodies, and subsidiaries are large, often contain free-text commercial detail, and are not needed for a renewal digest.

- `vendor.name`
- `name`
- `agreement_number`
- `total_cents` and `currency`
- `end_date`
- `renewal_status` and `display_renewal_status`
- `department.name`
- `creator.first_name` and `creator.last_name`
- `agreement_link`
- `subcategories[].name` and `categories[].name` — kept only long enough to apply `--contractors` filtering (below), then dropped like the other taxonomy fields

**Contractor filtering.** After extraction, apply `--contractors` (see [Arguments](#arguments) for the detection rule): under `exclude`, remove contractor hits from the working set and report what was dropped; under `only`, keep just the contractor hits and drop the rest, reporting how many non-contractor hits were dropped; under `all`, do nothing. Do this before bucketing in step 5, so urgency buckets and the vendor sweep only ever see the filtered set.

### 5. Present the digest

Sort by `end_date` ascending and bucket by urgency:

```markdown
# Renewal Radar — <resolved department path>
Window: <today> → <end date> (<N> days) · Source: Zip (apollo.ziphq.com), live
Statuses: <status list> · Showing <N> of <total>
Contractors: <all | excluded (N dropped: names) | only (N non-contractor rows dropped)>

## Act now (≤30 days)
| Vendor | Agreement | Amount | Ends | In | Status | Owner | Dept |
|---|---|---:|---|---:|---|---|---|
| <vendor> | [<name> (#<number>)](<agreement_link>) | <amount> | <date> | <days>d | <display status> | <owner> | <dept leaf> |

## Plan (31–90 days)
<same table shape>

## Watch (91–<N> days)
<same table shape>

## Unconfirmed — other departments matched "<TEAM>" (diagnostic only, not part of this digest)
<only under the permission-denied fallback; never merge into the tables above or into any total>

## PO-only renewals (no visible Agreement record)
| Vendor | PO(s) | Amount | Ends | Note |
|---|---|---:|---|---|
| <vendor> | [#<po_number>](<purchase_order_link>) | <amount> | <end_date_str> | Formal agreement not resolvable by vendor GUID or agreement number under this token |
<only when step 3.3 found a PO but no resolvable Agreement; list every PO found rather than picking one when ambiguous, and say so>

## Tracked vendors with no visible agreement
<only when the vendor sweep ran and found gaps>

**Scope caveat:** Zip returned only agreements visible to <caller email>. Contracts
filed by Procurement or other owners may not be included. Treat this as a floor,
not a complete inventory.

**Notice-deadline caveat:** `end_date` is the contract's term end, not the
cancellation notice deadline. Per Zip's own MCP documentation (ticket FIO-1440),
`auto_renews`, `opt_out_date`, and `renewal_workflow` exist in Zip's data model
but are deliberately not returned by the API yet — the underlying DB columns are
misleadingly named, and Zip's CLM team is renaming them behind a feature flag
before exposing them. This is a Zip product gap, not a permissions issue this
skill can work around. A contract bucketed as "Watch" (91+ days out) can already
be inside or past its real notice deadline. Do not imply the reader has until
`end_date` to decide. For anything that looks like it might auto-renew, say so
and point to the underlying agreement/attachment (or
`/apollo-legal:vendor-negotiation-support`) to confirm the actual notice window
before treating the timeline as safe.
```

Formatting rules:

- Amount is `total_cents / 100` with thousands separators, rendered in the record's **own** `currency`. Never assume USD.
- `end_date` renders as a plain date. Drop the `T00:00:00Z` suffix.
- "In" is days remaining computed from today.
- Every row links its `agreement_link` (or `purchase_order_link` in the PO-only bucket).
- Omit a bucket heading entirely when that bucket is empty rather than printing an empty table.
- The scope caveat and notice-deadline caveat are not optional. Always print both.
- The "unconfirmed — other departments" bucket is diagnostic, not requested-team data. Keep it under its own heading, never in the same table as the "Act now" / "Plan" / "Watch" buckets, and never sum its amounts into a team total.
- Mark any row recovered by the step 3 vendor sweep (i.e. found via `vendor_guid`/`agreement_number_str`, not the step 4 query) with a trailing `†` after the vendor name, and add one footnote line beneath the tables: `† found via vendor sweep — Zip's per-row visibility can differ by which filter is used; this row was not visible to the primary department/creator-scoped query.` Omit the footnote entirely when no row needs it.
- The "PO-only renewals" bucket holds financial commitments, not contracts — never call a row there an "agreement" or apply `display_renewal_status` to it, since neither exists for these rows.
- Print the `Contractors:` header line every run, not only when filtering is active, so a reader always knows whether contractor engagements are in view.

### 6. HTML report (`--html` only)

Load [`references/html-report.md`](references/html-report.md) and follow it. Always print the terminal digest from step 5 first; the HTML report is written in addition to it, never instead of it.

## Guardrails

- **Strictly read-only.** Never create, amend, cancel, or otherwise mutate an agreement, purchase order, or request through these tools. This skill only lists and reads.
- **Never surface vendor tax IDs, bank or remittance details, or personal contact information**, even though `list_vendors` and `get_vendor` payloads may contain them. Report the vendor name only.
- **Do not echo commercial free text.** Request descriptions, business cases, and PO memos often carry rate cards, headcount detail, and negotiation context. They are outside the field list in step 4 for that reason.
- **If any Zip call errors, say so plainly.** Report the failing call and the error. Never infer, interpolate, or fabricate a digest from partial data.
- **The "unconfirmed — other departments" bucket (permission-denied fallback) exists to catch mis-filed team contracts, not to broadcast unrelated departments' vendor spend.** If the digest is being pasted somewhere wider than the person who ran it (a channel, a doc, a ticket), drop that bucket first and keep it only in what the requester sees directly.

## Related Skills

- [`/apollo-legal:vendor-negotiation-support`](../../../apollo-legal/skills/vendor-negotiation-support/SKILL.md) — once a specific renewal needs a negotiation strategy, pricing analysis, walk-away points, or vendor-facing language, hand off there. This skill only tells you what is coming due; it does not model the deal.
- [`/apollo-procurement:procurement-faq`](../../../apollo-procurement/skills/procurement-faq/SKILL.md) — for policy, approval-threshold, and process questions such as who approves a purchase or how to file a renewal request. This skill reads Zip data; it is not an authority on Zip process.
