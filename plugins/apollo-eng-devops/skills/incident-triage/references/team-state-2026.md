# Team State Snapshot — 2026

A **point-in-time snapshot** of org structure that `apollo-dev-teams.yml` and CODEOWNERS lag behind. The registry is canonical for emails / Slack / EMs, but headcount allocation and team renames take weeks to propagate. When this file disagrees with the registry, **prefer this file for routing**, but explain the override in the proposed-comment so the user can validate.

**Update cadence**: hand-edited at the end of any triage session where a routing decision was wrong because of registry drift. Date the section. If this file gets older than 90 days, treat it with skepticism.

**Last updated**: 2026-05-23.

## The "registered vs functional" rule

A team membership in `apollo-dev-teams.yml` says nothing about what an engineer is *actually working on this quarter*. Two ways the registry misleads:

1. **Multi-team membership**: an engineer appears under multiple team entries (legitimate — many do). The registry doesn't say which is primary.
1. **Stale assignment**: an engineer rotated to a new functional team but their old entry was never removed.

Before auto-assigning an incident based on registry membership, check this file for the "supporting other teams" or "functionally on X" annotations below. If present, surface that to the user — don't silently stage the assignment.

## Recent organizational changes

### 2026 Q2 — CRM Platform team dissolved → succeeded by `deals-intelligence`

- **What happened**: CRM Platform team merged into `deals-intelligence` (EM: **Andrii Savchenko**). All former CRM Platform engineers now sit on deals-intelligence.
- **Registry state**: `apollo-dev-teams.yml` still lists a separate `crm-platform` entry with full duplicated roster (Rishabh Gupta, Nithin Reddy, Marcin Natanek, Anton Kononenko, Jephte Francois, Timmy Ho, etc. appear under both). `deals-intelligence.packs_owned` does NOT yet include `crm_platform` — listed only as `['deals']`.
- **CODEOWNERS state**: `packs/crm_platform @apolloio/crm-platform` (stale; should be `@apolloio/deals-intelligence`).
- **Routing rule**: any ticket touching `packs/crm_platform/**` routes to `deals-intelligence` regardless of what CODEOWNERS says.
- **Best individual reviewers** (by recent commit activity):
  - `packs/crm_platform/spec/controllers/api/v1/accounts_controller_spec.rb`: **Rishabh Gupta** (3 recent commits in 2026)
  - `packs/crm_platform/` overall (this week): Nithin Reddy, Marcin Natanek, Rishabh Gupta, Anton Kononenko, Jephte Francois
- **Hygiene item**: file PR to apply this to `apollo-dev-teams.yml` + CODEOWNERS. Not done yet.
- **Jira Impacted Team**: `Deal Intelligence` (not "Platform" and not "CRM Platform")
- **Slack**: `#xfn-team-deals-intel` (`C055RNHAK5Y`)

### 2026 Q1–Q2 — FE Platform partially absorbed into `fabric-surfaces`

- **What happened**: roughly half of `frontend-platform` engineers migrated to `fabric-surfaces`. Mohamed Djadoun is EM on both teams (which is the strongest signal it's a controlled split). NOT a clean rename.
- **Split shape**:
  - **Foundation work** (`package.json`, `tsconfig.json`, `eslint.config.js`, `packages/*`, top-level reducers in `assets/app/reducers/index.ts` and `slices/*`, `apiAction.ts`) stays with `frontend-platform`.
  - **Surface work** (presentational React components, domain UI shells) consolidated into `fabric-surfaces`.
- **Membership shifts** (per `apollo-dev-teams.yml` as of 2026-05-23):
  - On both: **Mohamed Djadoun** (EM both), **Rahul Tiwari**, **Vamsi Krishna**.
  - `frontend-platform` only: Pankaj Sati.
  - Spread elsewhere: Umang Galaiya (growth-pricing, call-commander, mobile-app, ai-transformation), Sid (ai-transformation).
- **Routing rule of thumb**: file touches build config / shared infra / `apiAction.ts` → `frontend-platform`. File touches a presentational React component / domain UI → `fabric-surfaces`. When unsure, ping Mohamed.

## BE Platform team (`be-platform`)

EM: **Ray Li** (also on `devops`). Slack: `#squad-eng-backend-platform` (`C0316SPCRMJ`). Jira impacted team: `Platform`. Default project: `PLAT`.

| Name | GitHub | Functional team annotation (2026-05) |
| ---- | ------ | ------------------------------------ |
| Ray Li (EM) | `@3mammoth` | EM both `be-platform` and `devops` |
| **Ken Mercado** | `@mightymercado` | **Functionally on DATA project work.** Active sprint: DATA-3056 (26Q3 Scrape Microsoft directory) + DATA-3291 (technologies extraction). Has historical context on `Crawler::SearchEngineLinkedinPersonUpdaterWorker` from prior firefighting (INCIDENT-28094 series) but **do not auto-assign him PLAT incident work**. Surface his current allocation when proposing him as an assignee. Registered on both `devops` AND `be-platform`. |
| **Neil Ongkingco** | `@neil-ongkingco-apollo` | **Supporting other teams** — ‹specifics to be added by user›. Don't auto-assign PLAT work; ask before proposing him. |
| Rafik Farhad | `@RafikFarhad` | Active on `be-platform` PD/INCIDENT triage. Recent activity on `packs/crm_platform/` overlap and various INCIDENT close-outs. |
| Lukas Linhart (`Almad`) | `@Almad` | Heavy active load on Sidekiq OOM + slow-test pattern (INCIDENT-29135, 29242, 29287, 29300, 28390, 29294). Avoid stacking more onto him without checking. The name "Almad" in `apollo-dev-teams.yml` is Lukas's GitHub handle, not a separate person. |
| Duncan Bryce | `@db11235` | Marked `primary_team: false` in registry — actively works elsewhere; loop in selectively. |
| Prasad Prabhu | `@prasad-apollo` | Active on `packs/billing/` + `packs/crm_platform/` adjacent work. Owns INCIDENT-29017 (apdex / FieldValueResolver), 29505 (assigned 2026-05-23). |

## DevOps / Infrastructure team (`devops`)

EMs: **Ray Li**, **Ralph Pyne**, **Adam Blackwell**. Slack: `#xfn-team-devops` (`C69FJ9NEM`). Jira impacted team: `Infrastructure`. Default project: `INFRA`.

| Name | GitHub | Notes |
| ---- | ------ | ----- |
| Ray Li (EM) | `@3mammoth` | EM both `be-platform` and `devops` |
| Ralph Pyne (EM) | `@rapyne` | DevOps EM |
| Adam Blackwell (EM) | `@adzuci` | DevOps EM (typical session-running user for this skill) |
| Ken Mercado | `@mightymercado` | See BE Platform table — functionally on DATA project work, not DevOps incident work. |
| Rafik Farhad | `@RafikFarhad` | Active on PD/INCIDENT close-outs. |
| Rajesh Dhakad | `@rajesh-dhakad` | DevOps IC. |
| Hari Vanga | `@hariapollo` | DevOps IC. Often the PD ack-er on devops-high-priority alerts (e.g. INCIDENT-29450 Mongos health). |
| Marcelo Mendonca | `@mtmendonca` | DevOps IC. Recent RCA owner on SEV-1 indexer latency (INCIDENT-29204). |
| Roshan Kumar | `@rshn20` | DevOps IC. |
| Apollo Devops Bot | `@apollo-devops-bot` | Service account — files tombstone PRs, registry hygiene. Not a person. |

## Routing implications

When `<scope> = team` resolves to `devops` or `be-platform`, apply these adjustments before staging assignments:

1. **Filter out Ken and Neil from default candidate lists** for PLAT-class incidents. Surface them only with the "currently working on X" annotation.
1. **Lukas overload guard**: if Lukas already has ≥4 open Platform tickets, do not propose him for new assignments without flagging the load to the user.
1. **Cross-team membership disambiguation**: when Ray Li or Ken appear as candidates, name which team you're proposing them under (devops vs be-platform) and which kind of work they're currently doing.
1. **Adam (the user)**: if `assignee = currentUser()`, don't double-route an incident to Adam if he's already running the triage session — propose another assignee.

## Open questions to resolve in the next update

1. What teams is Neil supporting? (Surfaced in 2026-05-23 session; not captured here yet.)
1. Is Ken's BE Platform / DevOps dual membership a permanent state, or is one of them slated to be removed?
1. Are there other teams in similar reorg states (data-platform, ai-apps, conversation-intelligence)? Add entries as they're discovered.
