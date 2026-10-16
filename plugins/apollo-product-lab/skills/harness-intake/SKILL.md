---
name: harness-intake
description: "Turn one sentence about a product or feature into the harness plan for the person's role, without them choosing stages or artifacts. Asks new product / feature in a harness initiative / change to an existing Apollo product, sizes the change (high, medium, low), maps current behaviour and owning teams, picks lenses, reads the PRD, design or ERD that already exist and asks only the decisions they leave open, and starts the plan's local steps in parallel without waiting for a go (doc 49). Activate on /harness-intake STATEMENT [--initiative SLUG] [--run RUN_ID], or when the person names a product or feature they want the harness to build or change (for example, we need to build FEATURE, start on FEATURE). A passing let's change inside a non-harness design or edit task is not a trigger."
---

# Harness intake

The person tells you what they want in one sentence. You decide what the harness produces for their role.
Read first: `${CLAUDE_PLUGIN_ROOT}/framework/40-work-sizes.md`, `17-decide-stage.md` §2.1, `34-harness-council.md`
§2, the profile `~/.claude/harness-profile.yml`, and the initiative's `harness-manifest.md` and `runs/*/index.md`
if they exist.

## Steps

0. **Storage, repo state, sync, then the escape scan.** First resolve the storage mode (doc 45 §2): a
   session with no Bash and no Write tool is `notion`; otherwise run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect` (with `--surface` from the profile, and,
   when the profile came from Notion, `--profile <the fetched profile saved to a temp file>`) and print
   its `say` line once. If that profile is used in `local` mode (claude.ai/code with `storage: local`),
   export `HARNESS_PROFILE=<that file>` before any `record-sync.sh` call so team sync sees it (doc 45 §4). In `notion` mode every `.ai/<initiative>/...` path below names a record
   page under the initiative's records root (doc 45 §3; create the root, `Harness record: <initiative>`,
   under `notion_parent` if it does not exist and record its URL as `notion_records_root`), records are
   written with `storage.py to-notion` and read with `notion-fetch` plus `storage.py from-notion`, and
   git, gh, `record-sync.sh` and the escape scan are skipped (the scan needs `gh`). In `local` mode,
   resolve the repo root with `git rev-parse --show-toplevel` (doc 43 §10); every `.ai/` path below is
   relative to that root.
   - **No git repo** with the profile forcing `storage: local`: say "no-repo mode: the plan stays in
     this chat; no snapshot, ledger, git or gh steps" in one line, skip every step below that reads or
     writes `.ai/`, runs git or gh, or calls `record-sync.sh`, and give the plan table in chat. Without
     that override the detector picks `notion` and the plan is recorded there.
   - **A repo with no `.ai/` at its root**: the harness is not initialised here. That is fine: the
     plan's first step is the bootstrap (step 2b, or `/product-harness-init` for a new product), which
     creates `<root>/.ai/`. Skip sync and the scan.
   - **A repo with the initiative's folder**: in team mode, if `.ai/<initiative>/` has no local
     changes, run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-sync.sh" pull <initiative>` first; if it
     has local changes, do not pull and say so. Then run the scan mode of
     `${CLAUDE_PLUGIN_ROOT}/skills/harness-escape/SKILL.md` (cheap: stamped PRs updated since the last
     scan, at most 20) and report new candidates in one line. Scan changes are committed with the
     intake record in step 6.
1. **Read the statement and the state.** Persona from the profile. Initiative: named, or inferred from the
   statement against `ls -d .ai/*/`; if none matches, this is a new initiative. Existing artifacts: PRD,
   estimate, constraint or legal register, design, ERD or plan, tracker epic, prior research, prior runs.
   **Context first (doc 49 §3):** read every artifact found and write the `A.context` snapshot (facts with
   sources, decisions already made, contradictions) and record `persona:` in its frontmatter. The grill is mandatory for every persona. Load that
   persona from `framework/templates/grill-checklist.yml` and add `## Grill` with exactly one line per
   required item: `- <item>: <answer> (source: <doc|user|code path>)` or `- <item>: deferred: <reason>`.
   Facts available in artifacts or code are looked up, never asked. Ask only unresolved decisions, one at a
   time, with the recommended answer first. Run `grill-check.py <snapshot> --persona <persona>` before
   continuing; exit 2 means intake is incomplete. A full `grill-me` interview remains only for a genuinely
   ambiguous idea with no artifacts. Stages an artifact covers are marked `covered by <artifact>` in the
   plan, not re-run.
1. **Which case, then size it** (doc 40, doc 43 §6 and §7). Ask, unless the statement already says:
   a new product, a feature inside an existing harness initiative (it has `.ai/<initiative>/`), or a
   change to an existing Apollo product with no harness folder. Then size the whole change, including
   related PRs, highest trigger wins: **high** (new product, new data class, consent, money, auth or
   permissions, a contract between teams, deletion of customer data), **medium** (any other behaviour
   change, a new endpoint, a new job, a schema or index change, a change in a surface owned by another
   team), **low** (only when tests can show the output is unchanged and no trigger applies). List facts
   you do not know yet and call it medium until they are known. A new provider, data class, consent
   behaviour or authority change is product-size even inside an old initiative. Say the case, the size
   and the trigger in one sentence. Reclassify against the actual diff before review.
   2b. **Existing behaviour and owners** (doc 43 §4, §5), for a change to existing behaviour. Bootstrap a
   light initiative when there is no harness folder (no new agents): create `<root>/.ai/<slug>/` with a
   `harness-manifest.md` that records `escape_maintainer:` (ask once: "Who adjudicates escapes for this
   work? Usually the EM."; write the answer, or `unowned` and say so) and `notion_parent:`. Its first snapshot is the
   **current behaviour map**: the real code path end to end with functions and the specs that cover
   it, every pass or option the change would add, where author-supplied configuration is validated
   (save time by default), the protections the existing path already applies to resolved values (they
   stay, unless an owner says otherwise), and the regression cases. "No existing path" needs the list of what was
   searched. Then the **owners**: run the repo's own matcher on the files the map names
   (`ApolloDevTeam.team_to_sensitive_files_hash` in `packs/util/lib/apollo_dev_team.rb`, for example
   `docker exec rails bin/rails runner 'p ApolloDevTeam.team_to_sensitive_files_hash(%w[<files>])'` in leadgenie; if Rails is not
   available, read `apollo-dev-teams.yml` sensitive entries and mark the row `unverified`) and match the
   behaviour against `surface-owners.yml`. Sensitive behaviour with no file match still gets an owner
   row. Each owning team other than the author's gets a plan row: owner assessment needed before the
   disputed behaviour is coded, with the answer (`approved`, `changed`, `not needed`, who, when)
   recorded in the snapshot. Posting a design in a channel is not a review.
   2c. **Lenses, by what the change affects** (doc 34 §2a): backend code adds backend; a query, schema or
   index adds db-perf; another team's surface adds an owning-team lens with that team's
   `platform-rules.md` rows. Product and UX only when users will see different behaviour, then one
   combined competitor and AI opportunity page; research only when the area has no prior research;
   the adversary for every medium and high change. For **medium and high**, schedule one consolidated
   cross-family review of the design artifact and one of the PR diff, before human review (doc 43 §6),
   and say in the plan which route will run or that no second family is reachable. The PR review is the
   existing PR adversary (`/codex:adversarial-review`, harness-council pr kind), not an extra reviewer;
   the design review is the council adversary on the design artifact. Each is at most two passes (full change, then the delta), with prompts of 15,000 characters or fewer (doc 46 §4, §5).
3. **Decide what to produce, by role.** Write the plan as a table: artifact · exists? · who produces it ·
   command · gate.
   - **PM**: no PRD → Stage B research (internal record via Glean, codebase reality, web) **and the
     competitive lens** (how the named competitors do it, pros and cons, options) **and the AI opportunity
     lens** (doc 42: per journey step, what a suggestion, score, explanation, generator, assistant or
     automation would do for the user, with a now / next / never question) → `/apollo-rnd:prd-one-pager`
     from those snapshots → `harness-council prd`. PRD exists → audit-lite, competitive lens, AI opportunity lens, council on the
     delta. That full research and both full lenses are for a **new product**. For an **enhancement** to an
     existing product they shrink as step 2c says: research only when the area has none, and one combined
     competitor and AI opportunity page only when users will see different behaviour. Always: the metrics spec, and the compliance checks the constraint register names for this surface.
   - **Designer**: the designer may start from only a thought or a PRD; a Figma file is not required.
     The designer's artifact is a Figma file, a Fabric Studio prototype or a Claude Design project
     (workbench from the profile); never ask a designer for a PR or a staging or preview link. The plan,
     in order, each step a snapshot:
     1. **Frame**: the job to be done, the user, the journey steps, from the thought or PRD (asserted
        facts marked `[ASSERTED]`).
     2. **Competitive analysis** (`product-reviewer` competitive mode): two or three competitors, cited.
     3. **AI lens** (`product-reviewer` AI-opportunity mode, doc 42): per journey step, where an assist
        shortens it, with a now / next version / never question.
     4. **Reuse audit**: the Fabric components that already do each part, from
        `node_modules/@apolloio/fabric-core/component-docs.md` and `docs/*.md`, the local `@apolloio/fabric`
        package, Storybook, and the Figma library (`search_design_system`); on claude.ai chat use Glean
        `code_search` and the Figma library, and mark rows `unverified` that no tool could open.
     5. **Platform lens** (`product-reviewer` platform mode, doc 47): the same flow already
        built elsewhere in Apollo (for example add to list, segment or saved search, subscriber
        selection, CSV import, which exists in several places), with one proposed reusable flow and the
        UX-parity rows each existing entry point needs.
     6. **Review panel**: `harness-council design` (or `prd` when there is no design yet) with the
        designer panel (council skill): research, product, engineering feasibility, UX, and the
        cross-family adversary where one is reachable.
        Then, once a prototype exists: prototype plan on the branch → Storyboard review → `design-diff` gap
        list (Code surfaces only) → `harness-council design`. Constrained copy check is mandatory when the
        register has copy rules. Steps 2 to 5 always run for a designer, also on an enhancement; they are
        one page each, not a research project.
   - **Engineer**: ERD or plan → roadmap lens → `harness-council erd|plan` → slices with the PR hygiene rules
     (doc 20 §8b: one PR per slice, target 15 files and cap 30 per PR, flags for new surfaces; the plan
     gives each slice its expected file count) → prepare the combined-preview link (and a px0 link when the person set px0 up; it is optional) without
     sharing them → PR council → the doc 50 pr-ready gate on the current head → only after it passes, hand
     those links to people (docs 20 §8f–§8g, 50). The build path
     runs inside the loop budget (doc 46): specs in the already-running app container (`docker exec`,
     never a fresh `docker run --rm` per run), indexes rebuilt only after an index change, commands from
     the repo's `CLAUDE.md` and skills (leadgenie: `SKIP_COVERAGE=1 bin/rspec`,
     `RSPEC_CREATE_MONGO_INDEXES=1` only after an index change, `ci-speed-run`); affected specs while
     iterating and the full relevant suite once before commit; mutation checks once at the end,
     behaviour changes only, at most 10 mutants, each against its own spec file; two cross-family passes (full,
     then delta), then the human; a loop report line in the build snapshot.
   - **QA**: test plan from the design snapshot (`feature-qa-wizard`), negative test per invariant, preview
     verification with Playwright → `harness-council verify`.
   - **End to end**: all of the above in stage order.
4. **Connect what this work needs.** From the statement, add the feature-specific sources to the profile's
   connectors and confirm each with a call (an incident follow-up needs Sentry; a customer-driven ask needs
   Enterpret; a metrics question needs Amplitude; anything with a legal register needs Notion). Do not
   proceed with a required source `absent`.
5. **Compliance, competitive and AI-opportunity checks are not optional.** If a constraint register exists, list the
   invariants this work touches. For a new product, schedule the competitive
   lens and the AI opportunity lens before build (for an enhancement users will see, the combined one-page form from step 2c) and state that the human will be asked for a go-ahead
   between approaches and a now / next version / never answer per proposed assist. Read
   `knowledge/ai-opportunities.md` if it exists: list every `deferred` row whose needs this work now
   provides and put "still deferred?" for each into the plan; a rejected row is not re-proposed without
   new evidence, and you say so if the statement asks for one. Run the platform lens's quick sibling check
   (doc 47 §1): when the change adds or changes a capability, flow or backend service and a sibling exists
   elsewhere in Apollo, schedule the platform lens; otherwise write the lens row `platform lens: skipped`
   with the reason. Re-surface `deferred` rows of `knowledge/platform-opportunities.md` the same way.
6. **Write** `runs/<run-id>/intake.snapshot.md` (doc 33 template; `stage: A.intake`) with the plan table, the
   case, the size and its trigger, the behaviour map and owner rows, the lenses with the reason for each,
   the scheduled cross-family reviews, the sources connected, the checks, and the first command. Gate rows
   are `checked`, `failed`, `unverified` or `not applicable` (doc 43 §8). Publish its Notion page (doc 33 mirrors
   rule, `templates/notion-page.md`) and put the URL in `notion:`; the intake is not reported without it. Prepare one ledger event; append it locally in local storage, while in notion storage the `post-update.py` call appends it to the fetched ledger page. Run `post-update.py --stage A.intake --summary <three-to-five-line-summary> --links <snapshot-and-page-links> --issue <intake-jira-issue-if-any> --initiative <initiative> --run <run-id> --event <stage-event-id> --agent <stage-agent> --outcome <stage-outcome> --profile <profile>` and execute every call in its JSON plan. Put the Jira issue or `blocked:<reason>` result in the snapshot's `jira:` line when Jira is selected; with `both`, blocked Jira never prevents Notion. Then run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-sync.sh" push <initiative> "<initiative>: intake"`
   (no-op for solo; skipped in notion mode, where the record page is the write).
7. **Start, do not ask (doc 49 §1).** Show the plan, then start its local, reversible steps at once, the
   independent ones in parallel in one message, and stop at the first outward action, destructive action
   or human gate. Ask only the decisions the context left open. From here on, send the progress pulse
   (doc 49 §2) at least every 10 minutes and at every stage boundary.
1. Before sending any stage-end summary to the person, save the draft and run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-claims.py <report.md>`. Add evidence beside every claim it
   lists. On a surface without Bash, apply the same evidence rule manually and say the script could not run.

## Sub-agents

Send research (Glean, Notion, Jira, web), the current behaviour map and owner lookups across many files
to sub-agents so the main context lasts; keep the plan table, the questions and the confirmation in the
main session. Follow `${CLAUDE_PLUGIN_ROOT}/framework/51-sub-agents.md` (doc 51): depth at most 2, the depth line
first in every brief, dispatches sized by the token budget — intake's research fan-out uses the
profile's `council_budget` because it is council-shaped — with platform concurrency 20 as the
non-overridable hard stop and a go-ahead only when the estimate goes over budget, one retry, a depth-1
agent may run exactly one cross-family review CLI on its own artifact as a leaf, and reports of about
2,000 tokens with detail in a file under the run.

## Hard rules

- The person never chooses stages or artifacts here, and is not asked to confirm a plan before local work
  starts. If the plan needs a decision only they can make (which competitor set, which surface), ask that
  one question with options and a recommendation, and keep running the steps that do not depend on it.
- New initiative → `/product-harness-init <slug>` is step 1 of the plan; intake does not create agents.
- Fix-size work still gets the constrained-copy, consent, provider and data-class check before it is called a fix.
- A named engineer owns the approach. If their own knowledge disagrees with the plan, reopen the
  investigation instead of repeating the plan (doc 43 §8).
