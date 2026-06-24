# Internal Apollo Tooling

These are Apollo-built systems that file, classify, or auto-fix tickets — distinct from third-party vendors (see [`vendors.md`](vendors.md)). They often *create* the tickets the skill is triaging, and their behavior produces recognizable patterns the skill must handle correctly.

## Pantheon (Apollo Forge coding agent)

- **What**: Apollo's internal Pantheon coding agent at `https://pantheon.agents.apollo-forge.io/`. Picks up auto-classified flaky-test tickets and tries to fix them via PR.
- **How it shows up**: comments on flaky-test INCIDENT tickets shaped:
  - `🤖 Pantheon Agent - Initial Run Started` with a Pantheon run URL.
  - `🤖 Flaky Test Bot - PR Created` with a GitHub PR URL on `apolloio/leadgenie`.
  - `🔄 Flaky Test Bot - Retry Attempt N` (max 3 retries) with `Failure Reason: CI checks failed`.
  - `🔄 Pantheon Agent - Retry Run Started` after each PR CI failure.
- **Owner**: Apollo internal — see the Pantheon team for behavior bugs.
- **Known failure modes**:
  - **Misroutes real failures as flaky.** When a QE-generated ticket has labels `flaky_test` + `failed_production_pipeline` but the description quotes a concrete production-vs-code mismatch (e.g. "expire_after_seconds property does not match between code and production"), Pantheon will try to "fix" it as a flaky test and CI will keep failing because there's nothing flaky. This burns up to 3 retry cycles per ticket.
  - **Bot PRs that look correct but were generated against the wrong premise.** Even when Pantheon's diagnosis lands at a reasonable diff, the assumption it's a flakiness fix may be wrong. Always sanity-check the bot's PR description against the ticket's *description body*, not just the title.
- **Triage rule**: **trust the description, not the label.** When you see a flaky-test ticket, before reading the bot comments, read the failure quote in the description:
  - Quote describes a real production behavior mismatch or index drift → **not flaky**. Close the bot PR, route to the actual owner (often DevOps for index drift, the affected pack's team otherwise), strip the `flaky_test` label.
  - Quote describes a test-mocking issue, factory order dependency, or environment-leakage pattern → likely flaky; bot's PR is worth vetting.
- **Past examples**:
  - INCIDENT-29537 (Mongo index drift labeled `flaky_test` — PR #91898 retried 3× and failed; real fix is a prod `collMod`).
  - INCIDENT-29505 (real flaky from logger-mock setup-phase pollution — PR #91775 looks correct).
  - INCIDENT-29502 (real flaky from cross-spec `places` collection pollution — PR #91765 looks correct).

### When Pantheon runs but does not open a PR

A Pantheon run link in the description does not guarantee a PR. Known cases where no PR appears:

- **ES schema drift** (`es_index_checker_spec` failures): the spec asserts field-level parity between production ES schemas and a stored snapshot. When production has diverged, Pantheon cannot determine whether the branch or the prod snapshot is the source of truth, so it takes no action. Route to the owning team (Search Platform for `packs/search_es_indexers`). The fix requires a human: either regenerate the snapshot to match prod, or merge the branch change to prod first.
- **CI credential / environment gap** (e.g. `CloudDnsProvider`, Google Cloud auth errors in specs): the fix requires stubbing or mocking a credential provider in the spec setup, or changing CI environment config. This is not a code change Pantheon can author. Route to the pack owner to add the credentials mock.
- **`human_intervention` label set**: the Pantheon run started but an engineer opened a manual PR instead of waiting. Check for a recent PR from the engineer (search GitHub for the INCIDENT key) before waiting for a bot PR. The manual PR may be diagnostic only (e.g. adds response body to failure output) and not the root fix — read its diff.

If a Pantheon run link exists but no PR has appeared after ~24h, assume one of the above patterns and route to the owning team rather than waiting for a bot PR that won't come.

## Apollo Agent (auto-classifier)

- **What**: an auto-classifier (`apollo-agent@apollo.io`) that reads inbound Slack `#product-feedback` and similar channels, files INCIDENT tickets, and writes a "Prioritization / routing rationale" comment.
- **How it shows up**: tickets with reporter `Apollo Agent`. First comment is always titled `Prioritization / routing rationale` and explains the SEV/P assignment, duplicate search, and Impacted Team choice.
- **Known failure modes**:
  - **Coarse Impacted Team selection.** The agent defaults to broad teams (e.g. "Platform") when the actual cause is narrow (e.g. a Billing API gate or a Living Data endpoint). The rationale comment is usually honest about the coarseness — it'll say something like "general product latency/freezing across multiple surfaces" rather than naming a service.
  - **Conflates symptom and cause.** A user reporting "the product froze while editing emails" can be classified as a UI/Platform issue when the actual upstream is a backend API returning 422s that the frontend doesn't surface. Read the technical evidence (Grafana, traces, code) before trusting the agent's routing.
- **Triage rule**: treat the agent's `Impacted Team` as a *starting hypothesis*, not a conclusion. Verify with at least one of: CODEOWNERS check, trace data, or recent commit history before confirming the route.

## jira-bot

- **What**: service-account automation (`svc-jira-api-1@apollo.io`) that posts the Pantheon status comments above, manages assignment transitions, and runs some other internal Jira automations.
- **How it shows up**: comments under `jira-bot` author. Mostly noise from the user's perspective; the comments don't need triage action.
- **Triage rule**: skip jira-bot comments when reading ticket history. They're status pings, not signal.

## Quality Engineering service account (`svc-apollo-qe`)

- **What**: QE automation (`svc-apollo-qe@apollo.io`) that auto-files INCIDENT tickets when a CI test fails or hangs in production-pipeline runs.
- **How it shows up**: reporter displays as `Quality Engineering`. Description follows a template starting with `First occurrence - Rspec (N, M)` and a link to a GitHub Actions run.
- **Known failure modes**: same as Pantheon — labels `flaky_test` / `failed_production_pipeline` are applied indiscriminately to *any* failing test, including infra checks (index validators), contract checks, and real regressions. Don't trust the label.
- **Triage rule**: read the failure quote in the description before deciding action. See Pantheon entry for the label-vs-description rule.

## Apollo DevOps Bot (`@apollo-devops-bot`)

- **What**: service account (`devops+apollo-admin-bot@apollo.io`) that files registry hygiene PRs — tombstone removals, inactive route cleanup, scheduled maintenance commits.
- **How it shows up**: as a commit author in CODEOWNERS / `apollo-dev-teams.yml` / route file history. Mostly cleanup, no triage action needed.

## Automation for Jira (`Automation for Jira` app)

- **What**: native Jira automation rules that auto-set fields, transition statuses, and post panel-styled comments.
- **How it shows up**: panel comments (`type: panel`, `panelType: success`) noting things like "The Impacted Team field was set to X according to the mapping found for the PagerDuty service Y in the file `apollo-dev-teams.yml`." These are the same rationale comments that explain *automated* Impacted Team assignment.
- **Triage rule**: skim for the PD-service mapping note when classifying a PD alert ticket — it tells you which PagerDuty service the alert came from, which is usually the most authoritative routing signal.

## What's NOT in this file

- Third-party vendors → see [`vendors.md`](vendors.md).
- Security scanners (Kodem, Orca, Bugcrowd, Panther, claude-security) → see [`finding-sources.md`](finding-sources.md). Those are signal sources, treated by their own routing rules.
- The PagerDuty / Grafana / Atlassian MCPs the skill itself uses — those are tooling, not auto-filing systems.
