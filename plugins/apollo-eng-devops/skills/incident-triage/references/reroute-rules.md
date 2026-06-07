# Reroute Rules

This file decides one thing per ticket: **does it stay with the running user's team, or does it get rerouted?** It does not enumerate teams — that lives in `apollo-dev-teams.yml` and is resolved via `team-lookup.md`.

The skill is invoked by engineers from many teams. "Keep" and "reroute" are relative to the running user's team set (see identity resolution in `team-lookup.md`).

## The decision

For each ticket, after extracting the source label and affected paths (`finding-sources.md`):

```
affected_team_slugs = paths → CODEOWNERS → registry-valid slugs
my_team_slugs       = identity resolution result

if affected_team_slugs ⊆ my_team_slugs   → KEEP
if affected_team_slugs ∩ my_team_slugs   → KEEP + propose loop-in comment for co-owners
if affected_team_slugs disjoint with mine → REROUTE
if affected_team_slugs is empty           → ASK reporter (clarification comment)
```

The proposed action column in the triage table is one of: `Work this sprint` / `Loop in @other-team` / `Reroute → @other-team` / `Assign PD responder` / `Close (PD resolved)` / `Ask reporter` / `Mark FP` / `Close (no action)` / `Mark duplicate of <KEY>`.

## PD / Grafana alert routing

PD alerts (the bulk of the queue) route differently from code findings — there's no affected path to look up in CODEOWNERS. Use the order in `pd-alerts.md`:

| Signal | Action |
| ---------------------------------- | ------------------------------------------------------------------------------- |
| PD MCP available | Use PD service → owning team. Authoritative. |
| PD MCP absent + service-group tag | Use the bracketed tag (`[Infra]`, `[Growth]`, `[Engagement]`) as a heuristic only. |
| Alert names a worker/controller/endpoint | Resolve the symbol via CODEOWNERS (same as code findings). |
| PD `resolved` > 24h ago, Jira open | Propose `Close (PD resolved)` with `linked-pd-resolved` template. |
| PD `acknowledged`, responder named | Propose `Assign PD responder` (assignee = responder) + transition In Progress. |

## Source-label heuristics (security findings — which usually stay with DevOps/Infra)

These shortcut the CODEOWNERS lookup when the answer is obvious from the source + path shape. They are heuristics — CODEOWNERS still wins on conflict.

| Source label | Path shape | Heuristic |
| ------------ | ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| `kodem` | `Dockerfile`, base image refs | DevOps / Infra keeps (OS layer) |
| `kodem` | `terraform/` | DevOps / Infra keeps |
| `kodem` | `scripts/`, `tools/`, `bin/dev*` | Owner of the script (often Corp Eng); apply CVSS context downgrade |
| `kodem` | `packs/<x>/` | Resolve via CODEOWNERS — almost always reroute |
| `kodem` | `Gemfile.lock`, `package-lock.json` at repo root | Resolve via CODEOWNERS for the consuming app; transitive deps often Backend Platform |
| `orca` | Terraform / IaC | DevOps / Infra keeps |
| `orca` | GKE cluster / node pool | DevOps / Infra keeps |
| `orca` | Cloud Run service, GCS bucket on a service | Resolve via CODEOWNERS of the owning service repo |
| `bugcrowd` | App-code path | Reroute to pack owner; severity is trustworthy |
| `bugcrowd` | IaC / infra path | DevOps / Infra keeps |
| `panther` | Endpoint / laptop / SaaS account | Reroute to Corp Eng / IT (detection-rule owner) |
| `panther` | Production workload alert | Resolve via CODEOWNERS of the service repo |
| `claude-security` | Any | Treat as Bugcrowd |
| *(no label)* | Any | Propose reporter clarification — hygiene gap, do not auto-route |

## Cross-checking routes against registry drift

CODEOWNERS and `apollo-dev-teams.yml` are both lagging indicators. Teams reorg, packs change hands, and the registry takes weeks to catch up. Before staging an assignment or reroute, check three sources in this order:

1. **CODEOWNERS** in the affected repo (`apolloio/leadgenie/CODEOWNERS` for most cases). File-level overrides win over pack-level defaults.
1. **`apollo-dev-teams.yml`** — `packs_owned`, `files_owned`, `members` for the candidate team. Cross-reference recent commit authors against the team roster.
1. **[`team-state-2026.md`](team-state-2026.md)** — current org-change snapshot. Documents reorgs, team renames, "functionally on X" annotations, and explicit override rules.

**When sources disagree, team-state wins for routing decisions *only where it explicitly calls out a reorg, rename, or override for the affected pack/path/team*** — and always explain the override in the proposed-comment so the user can validate. If team-state is silent on the path (no matching annotation), it does not override anything: default to CODEOWNERS. Team-state does not blanket-override CODEOWNERS; it overrides only the specific cases it documents.

### Worked example: CRM Platform disbanded → `deals-intelligence`

A ticket touches `packs/crm_platform/spec/controllers/api/v1/accounts_controller_spec.rb`. The three sources say:

1. **CODEOWNERS**: `packs/crm_platform @apolloio/crm-platform` → suggests CRM Platform.
1. **`apollo-dev-teams.yml`**: a `crm-platform` entry still exists with the original roster, BUT the same engineers also appear under `deals-intelligence` with the same EM. The packs_owned for `deals-intelligence` does *not* yet list `crm_platform`. Mixed signal.
1. **`team-state-2026.md`**: "CRM Platform dissolved → succeeded by deals-intelligence (EM: Andrii Savchenko). Any ticket touching `packs/crm_platform/**` routes to deals-intelligence regardless of CODEOWNERS. Best reviewer for `accounts_controller_spec.rb`: Rishabh Gupta."

**Result**: route to `deals-intelligence`, assignee proposal = Rishabh Gupta, comment cites the team-state override:

```proposed-comment INCIDENT-XXXXX
Per team-state-2026.md: CRM Platform was dissolved in Q2 2026; `packs/crm_platform/**` now routes to deals-intelligence (EM: Andrii Savchenko). Best individual reviewer for `accounts_controller_spec.rb` is Rishabh Gupta — 3 recent commits on this file. CODEOWNERS in apolloio/leadgenie still references @apolloio/crm-platform; that's a hygiene gap, not a current routing signal.
```

### When team-state overrides go wrong

If the team-state file looks stale (>90 days old) or contradicts active evidence (recent commits from engineers it claims aren't on the team anymore), drop to confidence `low`, mark the row `?`, and ask the user. Don't silently route based on a stale snapshot.

## When to KEEP even if CODEOWNERS points elsewhere

Rare, but legitimate:

- **Cross-team infrastructure dependency.** The finding is in another team's pack but the fix lives in shared infra (e.g. a Sidekiq queue config a pack depends on). Keep + comment naming the dependency.
- **Active incident in progress.** If the finding is the root cause of an open PD or active customer-impacting incident the user's team is responding to, keep until the IR closes — then re-route or close.
- **Reporter is on the user's team and explicitly tagged the user.** Treat as a request for help; keep + offer to pair.

## When to REROUTE even if CODEOWNERS points at the user's team

- **The user's team owns the file but a different team owns the misconfigured surface.** Example: a `packs/iam/` controller calling into an Engagement-owned service — the controller bug is yours, the service contract gap may belong to Engagement. Propose loop-in rather than full reroute.
- **The detection rule (Panther) lives in the user's team's repo but the alert is about another team's behavior.** Reroute to the team being detected, not the team owning the rule.

## When to route as `?` (ASK)

- Ticket is a one-liner with no service, repo, or path named.
- Reporter is unknown / external and the description is generic ("site is slow").
- Symptoms span multiple services with no clear primary, and CODEOWNERS lookup returns multiple disjoint teams.
- "Fix the security thing" with no source label, no CVE id, no scanner output.

For `?` rows, propose a reporter comment from `comment-templates.md` (`ask-reporter` block) — don't guess.

## When to mark as FP / close

- Kodem flagged an unscoped `Model.find` that the surrounding action correctly gates downstream (INCIDENT-28885-class false positive — though always audit the *whole* set of consuming actions before declaring FP).
- Orca flagged an intentional configuration documented elsewhere (e.g. Tailscale relay public IP — SEC-3287). Use `orca-accepted-risk` template.
- Duplicate of an already-triaged finding from the same source — link with `Duplicate` per `duplicate-heuristics.md`.

False-positive declarations always need Glean/PR evidence in the proposed comment. Never close as FP on a hunch.
