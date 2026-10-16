# 38 — Skill and plugin reuse map: what the pod already has

> Inventory date 2026-09-19. Sources: `.claude/skills/*/SKILL.md` (131 skills; 30 of them have a
> folded YAML description `>` and were classified from their body), the `apollo-plugins`
> marketplace (`SKILL_INVENTORY.md`, 20 plugins), `claude-plugins-official` (26 plugins),
> `openai-codex` (`codex` 1.0.6, installed), `thedotmack` (claude-mem, not installed).
> Installed: `apollo-eng@apollo-plugins` 1.1.0, `codex@openai-codex` 1.0.6.
> Regenerate the raw inventory with the script in §7; do not hand-edit counts.

## 1. Summary

- **The pod does not need new skills for most stages.** Of the 131 repo skills, 27 map directly
  onto a harness stage or a council lens and can be used as-is; 11 are worth wrapping (they do
  the right thing but assume a persona, a team, or a tool the harness must supply); the rest are
  team-specific operations (on-call, CRM debugging, data crawlers, extension release) that the
  harness should never call.
- **Three marketplace skills are the harness's own missing pieces**: `/apollo-rnd:prd-one-pager`
  (Stage C authoring for a PM), `/apollo-rnd:setup-fabric-studio` (designer onboarding, doc 39),
  and `/apollo-eng-experimentation:*` (Stage G metrics; the plugin is registered in
  `.claude/settings.json` but not installed on this host).
- **The Codex plugin is the second family, already installed.** `/codex:review` and
  `/codex:adversarial-review` are the PR-kind adversary without shunt; `codex-rescue` is the
  fallback when a Claude slice stalls. The council keeps shunt for the erd/plan kinds because those
  lenses need `Read/Grep` on the repo with a 400k window (doc 37); the Codex plugin runs in its
  own sandbox without the harness snapshots.
- **Overlaps to retire**: three PR-description/ship skills, two bug-bash generators, two
  QA-steps skills that the harness's VERIFY snapshot should call rather than reimplement, and
  `security-review` present both in the repo and in `apollo-eng`.
- **Gaps that are real**: no skill produces a metrics spec *and* wires the Amplitude events (two
  skills, no seam); no skill runs the designer's Fabric Studio diff against production (the
  ads-frontend agent does it in prose); no skill turns a Sentry or Amplitude signal into a
  feature-size run (doc 40) rather than an incident.

## 2. Reuse table — repo skills (`.claude/skills/`)

Verdicts: **use** (call as-is from the stage or lens), **wrap** (call, but the harness supplies
the input or reroutes the output), **skip** (team operations; not the harness's job).

### Stage A–B — audit and research

| Skill | Stage / lens | Persona | Verdict | Note |
|---|---|---|---|---|
| `artifact-audit` | A | PM, architect | use | Already the Stage A implementation (document graph). |
| `feature-to-metrics-spec` | B→C | PM | use | North Star + 3–5 metrics from a PRD; the product lens cites it. |
| `capacity-planner` | B (research lens: scale) | architect | wrap | Give it the ERD snapshot, not the PRD; it answers the S1–S7 posture questions from doc 17. |
| `product-reviewer` (agent) | council: product lens | PM | use | Competitor + reusability + lifecycle. |
| `generate-structured-ai-based-summary` | B | researcher | skip | Product feature, not a research tool. |

### Stage C–D — specify and design

| Skill | Stage / lens | Persona | Verdict | Note |
|---|---|---|---|---|
| `product-harness-init` | C/D scaffold | any | use | Entry point (doc 12). |
| `harness-onboard`, `harness-snapshot`, `harness-council` | all | any | use | The harness's own. |
| `design-diff` | D→F | designer, FE engineer | use | Prototype-vs-production gap list; inventory is deterministic, buckets are judged; reads the Storyboard. |
| `feature-qa-wizard` | D→G (QA plan from PRD/ERD/Figma) | QA | wrap | Feed it the D snapshot and the Fabric Studio branch, not Figma alone; its output becomes `G.verify.snapshot.md` §plan. |
| `bug-bash-generator` | G | QA | wrap | Same output as `/apollo-eng:bug-bash-generator`; keep the repo copy (tmp export works offline), drop the plugin call from docs. |
| `notion-bugs-and-tests` | G | QA | skip | Superseded by `bug-bash-generator`. |
| `pricing-variant-clone`, `pricing-add-on` | D/F | PM, FE | skip | Growth-specific. |

### Stage E — architecture council

| Skill | Lens | Persona | Verdict | Note |
|---|---|---|---|---|
| `db-performance-architect` + `db-perf` (agent) | db-perf | architect | use | Already the erd/plan db-perf lens. |
| `mongo-shard-collection` | db-perf | architect | use | Call for every new collection in an ERD; the Ads ERD did this by hand. |
| `backend-componentization` | architecture | architect | wrap | Pack boundary check on a new pack (`packs/ads`); run once at ERD time, not per PR. |
| `rails-console-safety` | plan | backend | use | Any backfill or one-off script in a plan goes through it before the human gate. |
| `slice-fit` | E→F | architect | use | Classifies slices agent-ownable / with-review / human. |
| `mongo-analyze-incident`, `mongo-index-discrepancies`, `mongo-unused-indexes` | ops | DevOps | skip | Incident and hygiene tooling. |

### Stage F — build

| Skill | Stage / lens | Persona | Verdict | Note |
|---|---|---|---|---|
| `tdd-loop` | F slice | engineer | use | The slice owner's inner loop. |
| `rspec-testing`, `unit-testing`, `playwright-e2e-generator`, `e2e-test-generator-local` | F | engineer, QA | use | Test authoring per layer; VERIFY cites which ran. |
| `ci-speed-run` | F | engineer | use | Local spec selection before push (doc 46 §2). |
| `backend-quality`, `frontend-quality` | F self-review | engineer | use | Run before `code-review`. |
| `code-review` (supervisor) + `backend-reviewer`, `frontend-reviewer`, `security-reviewer`, `pr-tech-lead-synthesizer` | council: pr kind | engineer | use | The pr-kind council is this skill; doc 34 §2 should say so instead of listing lenses twice. |
| `deslop`, `code-simplification` | F post-slice | engineer | use | Run after the slice is green, before review. |
| `fix-component-performance`, `fix-unstable-hooks` | F FE | engineer | use | Gated by the CLAUDE.md perf-risk rule. |
| `i18n-fixes` | F FE | engineer | use | Prototype strings are hard-coded; this is the port step. |
| `auto-pr`, `ship-it`, `codeowners-split-prs` | F→PR | engineer | wrap | Three overlapping PR pipelines. Harness uses `codeowners-split-prs` for the FE/BE split (memory: separate PRs) and `ship-it` for the description; `auto-pr` duplicates the whole harness and is **skip** inside a run. |
| `dribble-dev-orchestrator`, `marksieglock-dev-orchestrator` | F | engineer | skip | Personal Jira workflows; same shape as a harness run without snapshots. |
| `make-it-work` | F/G debug | engineer | use | Systematic debugging when a slice or preview fails. |
| `portless-dev`, `local-be-server`, `dev-env-setup` | F setup | engineer | use | Listed in doc 39 as engineer connectors. |
| `feature-flag-cleanup`, `notification-cleanup`, `dead-code-audit` | fix size | engineer | use | Doc 40 fix-size examples. |
| `modularization-orchestrator-tick`, `module-extraction`, `shared-platform-lift` | F | platform | skip | FPLAT programme tooling. |

### Stage G — verify

| Skill | Stage / lens | Persona | Verdict | Note |
|---|---|---|---|---|
| `qa-steps-for-eng`, `qa-steps-for-non-eng` | G | QA, PM | wrap | Both read a PR; the harness passes the PR plus `G.verify.snapshot.md` so steps cover negative tests (doc 21 §4). One skill with an audience flag would replace both. |
| `manual-test-execution` | G | QA | wrap | Body is Notion-DB specific; keep for teams that use that DB. |
| `playwright-cli`, `playwright-trace`, `playwright-testing` | G | QA | use | Preview verification tooling. |
| `apollo-mcp-promptbook`, `headless-mcp-bug-bash` | G | QA (Headless) | skip | Squad-specific. |
| `*-flaky-jira-fixer` (rspec, vitest, playwright), `flaky-test-self-learner` | CI | engineer | use | Fix-size; called when CI is red for a non-ads reason. |
| `product-ship-post` | G→launch | PM | use | Duplicate of `/apollo-eng:product-ship-post`; keep the repo copy. |

### Operations — never called by the harness

`alarm-breach-remediator`, `customer-resolution`, `incident-diagnosis`, `oncall-*`, `*-oncall-handoff`,
`rep-oncall-weekly-report`, `living-data-oncall-summary`, `sidekiq-analyze-retryset`,
`ddos-alert-investigator`, `dialer-triage`, `workflow-debugger`, `integrations-crm-job-debugger`,
`salesforce-crm`, `zoho-crm`, `entity-matcher-debugger`, `contact-account-upsert-debugger`,
`crm-error-frequency`, `es-reshard-indices`, `data-*-technologies-*`, `liveintent-ip-hem-pipeline`,
`pipedream-connector-ingress`, `extension-*`, `chrome-page-profiler`, `*-perf-regression-rca`,
`frontend-crash-rca-fixer`, `backend-apdex-backtest`, `support-mcp-tool-docs`, `update-public-api-docs`,
`update-apollo-agent-task`, `upload-agent-sessions`, `phone-number-analysis`, `infosec-finding`,
`legal-queries`, `in-progress`, `test-dedup-optimize`, `observability-coverage-tick`,
`grafana-*`, `team-observability`, `inbound-*`, `meeting-assistant`, `conversation-insights`,
`growth-pricing-and-packaging`, `workflow-pr-review`, `find-recent-prs-for-component`,
`automate-amplitude-event`, `dashboard-digest-routine`, `learn-from-chat`, `self-review`,
`deep-insights`, `framework-phase-review`.

Two exceptions inside that list: `team-observability` and `grafana-dashboard` are **use** at the
end of Stage G when the PRD names a dashboard as a launch deliverable; `learn-from-chat` is
**use** at the end of every run to fold corrections into memory (doc 43, learning loop).

## 3. Reuse table — marketplace plugins

| Plugin skill or command | Stage / lens | Persona | Verdict | Note |
|---|---|---|---|---|
| `/apollo-rnd:prd-one-pager` | C authoring | PM | **use** | The only PRD author in the estate; structured intake + Glean evidence + Notion. Stage C "authoring" disposition should call it. Requires installing `apollo-rnd`. |
| `/apollo-rnd:setup-fabric-studio` | onboarding | designer | **use** | Replaces the hand-written setup in doc 39 §designer; `/harness-onboard` calls it. |
| `/apollo-eng-experimentation:create-amplitude-experiment`, `experiment-metrics-dashboard`, `experiment-cleanup` | G metrics | PM, engineer | **use** | Registered in settings, not installed here. Stage G's metrics check should call the dashboard skill. |
| `/apollo-eng:plan-from-jira` | feature intake (doc 40) | engineer | **wrap** | Its plan is a flat list; the harness needs it written into `feature-manifest.md`, so `product-harness-init --feature` calls it and rewrites. |
| `/apollo-eng:mongo-pr-guard` | pr council: db-perf | engineer | **use** | Production-incident patterns (unsharded collections). Complements `db-performance-architect`, which is static review; run both on the pr kind. |
| `/apollo-eng:security-review` | pr council: security | engineer | skip | Same as repo `security-review`; use the repo one. |
| `/apollo-eng:pr-description`, `product-ship-post`, `bug-bash-generator` | F/G | engineer, PM, QA | skip | Duplicates of repo skills. |
| `/apollo-eng:rca-doc-review` | fix size follow-up | engineer | use | When a fix run is an incident follow-up. |
| `/apollo-eng-fabric-surfaces:pr-analytics-review` | pr council: product | PM | **wrap** | Finds missing Amplitude events on a PR; the product lens on the pr kind should call it. Squad plugin, so install by hand or lift into `apollo-eng`. |
| `/apollo-eng-devops:systematic-debugging`, `wtf-does-this-do`, `which-model` | F debug, onboarding | any | use | `which-model` is a manual companion to `models/model-registry.yml`; it does not replace it. |
| `/apollo-eng-leadership:okr-report`, `eng-metrics`, `sprint-planning` | outside runs | EM | skip | Management reporting. |
| `/apollo-product:product-overview` | onboarding | PM | use | Read once by a PM persona in `/harness-onboard`. |
| `/apollo-analytics:*` (`product-debrief`, `metric-lookup`, `data-catalog-search`) | B research | PM, researcher | **wrap** | Governed Snowflake metrics through Jarvis; the research lens should cite them as `[P]` internal facts. Needs the Jarvis MCP; see doc 39. |
| `codex@openai-codex`: `/codex:review`, `/codex:adversarial-review` | pr council: adversary | engineer | **use** | Second family with no shunt. Output is a chat result, so the lens must copy it into `council.<slug>.adversary.md` (doc 33) before the synthesizer reads it. |
| `codex@openai-codex`: `codex-rescue` (agent), `/codex:transfer` | F stall | engineer | use | Hand a stuck slice to Codex with the snapshot path as the brief. |
| `codex@openai-codex`: `gpt-5-4-prompting`, `codex-cli-runtime`, `codex-result-handling` | reference | any | use | Read by `scripts/gen-codex-agents.sh` authors; the model id in it is stale (gpt-5.4) versus the registry's gpt-6-astra. |
| `claude-plugins-official`: `feature-dev`, `pr-review-toolkit`, `code-review`, `code-simplifier`, `frontend-design` | F | engineer | skip | Generic; the repo's Apollo-aware equivalents exist for each. |
| `claude-plugins-official`: `hookify`, `plugin-dev`, `claude-md-management` | framework maintenance | framework author | use | For the gate hooks in doc 12 §6 and for packaging the harness as a plugin (doc 35). |
| `claude-plugins-official`: `ralph-loop` | F long slice | engineer | skip | Unbounded loop conflicts with the snapshot-per-stage rule. |
| `thedotmack` claude-mem | memory | any | skip | Not installed; the harness's memory is the file memory plus snapshots, and a second store would fork the record. |

## 4. Overlaps to resolve

| Overlap | Keep | Retire or redirect | Why |
|---|---|---|---|
| `auto-pr` / `ship-it` / `codeowners-split-prs` / `/apollo-eng:pr-description` | `codeowners-split-prs` then `ship-it` | `auto-pr` inside runs; plugin `pr-description` | One split rule (FE and BE PRs) and one description writer. |
| `bug-bash-generator` (repo) / `/apollo-eng:bug-bash-generator` / `notion-bugs-and-tests` | repo `bug-bash-generator` | the other two | Repo copy has the offline export. |
| `qa-steps-for-eng` / `qa-steps-for-non-eng` | both, for now | merge into one with an `--audience` flag | Same input, same gaps (no negative tests). |
| `security-review` (repo) / `/apollo-eng:security-review` | repo | plugin | Identical body. |
| `product-ship-post` (repo) / plugin | repo | plugin | Identical body. |
| `code-review` supervisor / doc 34 pr-kind lens list | `code-review` | doc 34 lists lenses that are already its sub-agents | Doc 34 §2 pr row should read "runs `code-review`, adds the Codex adversary". |
| `capacity-planner` / doc 17 scale posture S1–S7 | both | none | Different depth; the posture table is the summary, the planner is the evidence. |

## 5. Gaps the estate does not cover

| Gap | Persona | Stage | Smallest fix |
|---|---|---|---|
| ~~Design diff: Fabric Studio prototype vs `packages/<pkg>/src` as a gap list~~ | designer, FE engineer | D→F | **Closed 2026-09-19:** `design-diff` skill (`scripts/inventory.py` deterministic inventory + judged buckets) and the Fabric Studio Storyboard view (PR apolloio/fabric-studio#348). |
| Metrics seam: `feature-to-metrics-spec` names events, nothing wires them until a PR exists | PM, engineer | C→F | Extend the spec skill to emit an `amplitude-events.md` the FE slice reads (pattern exists in `.ai/inbound-chat-assistant/04-amplitude-events.md`). |
| Signal-to-feature intake: Sentry/Amplitude/Enterpret finding → doc 40 feature run | PM | intake | `product-harness-init --feature --from <url>`; today the ask is typed by hand. |
| Negative-test plan from the constraint register | QA | G | `feature-qa-wizard` reads a PRD; give it the invariants table so C1–C6 style rules become test rows. |
| Cross-family PR adversary that writes a snapshot | engineer | pr council | Wrap `/codex:adversarial-review` so its output lands in `council.<slug>.adversary.md`. |

## 6. How the router finds these

Skills carry no frontmatter beyond `name` and `description`, so the router (`product-orchestrator`)
cannot resolve them structurally today. Two rules, no new mechanism:

1. **Agents** already carry `surfaces:` (doc 14 Q-O1). Add `skills:` listing the skills in this
   table an agent composes, with the verdict as a comment. The six harness agents get it now; the
   pre-existing agents stay prose-resolved.
2. **This document is the skill index.** The router reads §2 and §3 for the stage it is staffing
   and never invents a skill call that is not in a **use** or **wrap** row. A new skill enters the
   pod by getting a row here, with a verdict, in the same commit that adds it. Doc 36 quickstart
   links the persona column for each role.

## 7. Regenerating the inventory

```bash
python3 - <<'PY'
import glob, re, csv, sys
rows=[]
for p in sorted(glob.glob('.claude/skills/*/SKILL.md')):
    t=open(p,encoding='utf-8').read()
    m=re.search(r'^description:\s*(.*)$', t, re.M)
    rows.append([p.split('/')[2], (m.group(1) if m else '').strip()])
csv.writer(sys.stdout, delimiter='\t').writerows(rows)
PY
grep -E '^\| apollo-' ~/.claude/plugins/marketplaces/apollo-plugins/SKILL_INVENTORY.md
claude plugin list 2>/dev/null || ls ~/.claude/plugins/cache
```

Re-run before editing the counts in the header; a description that reads `>` is folded YAML and
needs the SKILL.md body read for its verdict.
