---
name: harness-onboard
description: "First-time (or refresh) onboarding to the product harness for any persona (product manager, designer, engineer, QA, researcher, EM). Picks the persona, checks which connectors and tools are present, walks the person through missing setup, writes ~/.claude/harness-profile.yml, and shows their flow: what to run, what they get, which gate they own, and how their work stays in sync with the other lenses through the council. Activate on onboard me to the harness, set me up as a designer/PM/engineer/QA, how do I use the harness, or /harness-onboard [persona]."
---

# Harness onboarding

You are talking to someone who may never have used the harness. Be concrete, one step at a time, and never make them read the framework docs to get started. Read first (yourself, not them): `${CLAUDE_PLUGIN_ROOT}/framework/36-roles-quickstart.md`, `39-connectors-setup.md`, `templates/harness-profile.yml`, and `models/model-registry.yml`.

**Repo state.** Many people run the plugin from Claude Desktop with no repo checkout. Resolve the repo root first with `git rev-parse --show-toplevel` (doc 43 §10); every `.ai/` path is relative to that root, not to the current subfolder. No git repo: say "no-repo mode" in one line and skip every repo, git, gh, docker and `.ai` step below (initiative listing, `harness-snapshot read`, tool checks for gh and docker). A repo with no `.ai/` at its root: list no initiatives and say intake can bootstrap one. Onboarding still asks the questions, connects the connectors and writes the profile. With no repo, or on claude.ai, the record and (where the home directory is not kept) the profile go to Notion instead of being skipped (doc 45).

## 0. The questions, all of them, up front

Ask these with `AskUserQuestion` when it is available (one call, several questions), otherwise as one
numbered list. Do not start detecting or writing until they are answered:

0. **Where are you running this?** terminal (Claude Code CLI) / Desktop app, Code tab / claude.ai/code
   (or a Desktop cloud session) / claude.ai chat (uploaded Skills). It sets `surface:` and the storage
   mode (doc 45 §2, §5): terminal and Desktop Code tab → `storage: local`, profile in
   `~/.claude/harness-profile.yml`; claude.ai/code → records and profile in Notion (`storage: notion`,
   or `local` if they will commit `.ai/` on the branch); claude.ai chat → Notion for both, always. If
   this session has no Bash and no Write tool, it is claude.ai chat whatever the answer; say so. Skip
   what cannot work there: on claude.ai/code and chat, the second-family install (question 7 records
   `second_family: n/a-cloud`), the Fabric Studio setup and previews, Playwright against previews and
   docker; on claude.ai chat also git, gh and the plugin hooks. Say in one line what is skipped and
   which stages need a laptop (doc 45 §5).
1. **Who are you here?** product manager / designer / engineer / QA / researcher / EM / **end to end** (one person running the whole pod; you own every gate).
2. **Where should stage updates go?** Ask this as one tracker question, with the persona default first and
   marked recommended: engineer and QA → Jira; PM, EM and end to end → both; designer and researcher →
   Notion. The choices are Jira, Notion, or both. If Jira is included, require `jira_project`; optionally
   accept a default `jira_issue`. Reuse the existing `notion_parent` for Notion.
3. **Solo or team?** Will anyone else work on the same initiative with the framework?
4. **Which initiative?** An existing one in this repo (list `ls -d .ai/*/` for them), or a new one
   (ask for a short slug and the product name). This decides whether the next step is
   `/harness-snapshot read` or `/product-harness-init`.
5. **What kind of work?** A new product / a feature inside an existing harness initiative (it has a
   `.ai/<initiative>/` folder) / a change to an existing Apollo product that has no harness folder (the
   common case; doc 43 §7). Intake sizes the change later (high, medium or low, doc 43 §6); a new
   provider, data class, consent behaviour or authority change is product-size even in an old initiative.
6. **Which sources will you need?** Offer the doc 39 rows for their persona as checkboxes (Notion,
   Jira/Confluence, Figma, Fabric Studio, Glean, Amplitude, Enterpret, Sentry, Grafana, Playwright,
   Slack, GitHub CLI, Docker). Only the ticked ones are set up now; the rest stay listed as optional.
7. **Second model family, installed by default.** For every persona except designer and UX researcher this is not a question: onboarding installs the second family on a local host, because a council whose adversary is the author's own family is the failure the harness exists to prevent. Claude Code host: the Codex plugin (`/plugin marketplace add openai/codex-plugin-cc`, `/plugin install codex@openai-codex`, `/reload-plugins`, `/codex:setup`) and shunt (`/apollo-product-lab:harness-shunt setup`, which also runs `codex login`). Codex host: `npm i -g @anthropic-ai/claude-code` and `claude login`. Say what will be installed and why in two sentences and ask for one go-ahead for the whole block; if the person declines, record `second_family: declined <date>` in the profile and tell them every session-start line will say so and every council memo will be tagged same-family. Designers and UX researchers are asked once whether they also write code; yes means the same default applies, and no means no shunt, no Codex and no cross-family probe now or at session start (record `second_family: n/a-design`), unless they ask for it later. On a cloud host the block is skipped and `second_family: n/a-cloud` is recorded.
8. **Base model.** Detect the host (`claude` vs `codex`). Recommend the host's base model from the
   registry `hosts:` block (Claude Code: Fable 5.1; Codex: gpt-6-astra at xhigh for design and review
   work, medium for routine slices) and say why in one sentence. The profile entry is a record, not an
   override (doc 37 §3c): the session runs on what the host config says. So offer, with one go-ahead, to
   write it where the host reads it: Claude Code, `/model <id>` (Enter saves it to your user settings) or
   the `model` key in `~/.claude/settings.json`; Codex, `model = "gpt-6-astra"` and
   `model_reasoning_effort = "xhigh"` in `~/.codex/config.toml`. Say that a `/model` choice in a session
   still wins, and that council lenses pin their own model and effort regardless. If they want to keep
   their current model, record `base_model: kept: <model>` and move on; never insist. In the same go-ahead,
   **set the compaction point by default** (doc 37 §3b): Claude Code `/autocompact <about 0.6 × the model window>` (saved to user settings), Codex `model_auto_compact_token_limit` at about 0.6 × the
   window and `tool_output_token_limit`, and say in one sentence why: answers degrade past roughly 60%,
   and after a compaction the hook reloads the run record from disk automatically. Record
   `autocompact: <value>` in the profile; a person who wants the tool default records `autocompact: off`.
9. **Designers only: workbench.** Fabric Studio (default on terminal; real Fabric code, diffable against
   production), Claude Design (faster exploration, built-in comments, no code diff; the default on
   claude.ai/code and chat, where Fabric Studio previews do not open), or Figma-only through the Figma
   MCP. Record `design_workbench`. The Figma connector is required whichever they pick. Say the designer
   defaults once: you share a Figma file, a Fabric Studio prototype or a Claude Design project, never a
   PR or a staging link; you can start from a thought or a PRD with no Figma, and intake then runs
   competitive analysis, the AI lens, a Fabric reuse audit and a platformization check before the review
   panel (doc 45 §6).

Repeat the answers back in five lines before continuing. Persona **end to end** takes every persona's connector rows, first commands and gates.

## 1. Persona and how they will use the framework

Detect the host first: use question 0, then confirm with `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect --surface <answer>` when Bash exists (doc 45 §2) and print its `say` line. If `CLAUDE_CODE_REMOTE`/no `$HOME/.claude` writable laptop state, or the person says they are in claude.ai/code, record `host: claude-code-cloud`, skip the shunt and Fabric Studio walkthroughs (no VPN, no local process), point them at doc 39 "Design tools from a claude.ai/code session", and say which stages still need a laptop (Verify against the preview, Fabric Studio previews and comments, any cross-family council). Ask two things, not one: the persona, and **solo or team**. Team means someone else will work on the same initiative (product or feature) with the framework. Record `collaboration: solo | team` in the profile. If team, read doc 41 and apply its git sync rules: pull the initiative directory before reading any snapshot, commit and push after every snapshot, ledger event or decision record, and treat someone else's newer snapshot as the record. Say this back to the person in one sentence.

If not given, ask one question with the options: product manager, designer, engineer, QA, researcher, EM. Then say in two sentences what the harness does for that persona and which gate they own (doc 36). Make clear that every decision still goes through the council with the other lenses; a designer's work is not reviewed by the designer alone.

## 2. Detect what is present (deterministic, no guessing)

- **MCP servers declared by this plugin** (`${CLAUDE_PLUGIN_ROOT}/.mcp.json`: Notion, Atlassian, Slack, Glean, Figma, Claude Design, Sentry, Amplitude, Grafana; Playwright is opt-in, add it with `claude mcp add playwright -- npx -y @playwright/mcp@latest` only for QA and engineers; never for designer or UX personas, who work in Figma and Fabric Studio and do not need a browser driver): check `claude mcp list` for duplicates with servers the person already had; if a name appears twice, tell them which one to disable (Claude Code Settings → MCP, or `claude mcp remove <name>` for their own copy). Each server authenticates on first use; hand over the login prompt, never a code.
- **Connectors**: look at your own tool list. For each row in doc 39, a connector is `present` if its normal tools exist, `unauthenticated` if only `mcp__claude_ai_<Name>__authenticate` exists, `absent` otherwise. For unauthenticated ones the persona needs, call the authenticate tool and hand over the URL; do not proceed on their behalf.
- **Tools** via Bash, each a one-liner: `command -v codex`, `command -v px0 && px0 -version`, `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/` (shunt), `test -d ~/Code/fabric-studio || ls -d ~/*/fabric-studio`, `command -v gh && gh auth status`, `docker ps --format '{{.Names}}' | grep -x rails`, `test -f ~/.config/shunt/shunt.toml`.
- **Initiatives**: `ls .ai/*/harness-manifest.md` and each `runs/*/index.md`.

## 3. Walk the gaps, persona-first (and actually connect them)

**Hard rule:** a connector the persona or the stated work needs is not "listed", it is connected in this
step. For each one: give the command or click path, wait, then confirm with one harmless call (Notion
`search`, Atlassian `atlassianUserInfo`, Glean `search`, Amplitude `get_amplitude_context`, Grafana
`list_datasources`, Figma `whoami`, Playwright `browser_navigate`). Only a confirmed call makes it
`present`. The profile is not written while a required connector is `absent` or `unauthenticated`;
optional ones may stay listed as such. Required by persona: PM → Notion, Atlassian, Glean, Amplitude;
designer → Figma, Notion, Fabric Studio clone (or Claude Design MCP); engineer → GitHub CLI, Docker,
Notion, Glean; QA → Playwright, Sentry, Notion; EM → GitHub CLI; end to end → all of these. Intake
(step 5) adds the feature-specific ones (Sentry for an incident follow-up, Enterpret for a
customer-driven ask, Amplitude for a metrics question).

px0 is **optional** on every persona (it is offered as its own go-ahead below; a `declined` or
`n/a-cloud` record is a valid answer and does not block the profile).

**px0, opt-in, pinned.** For every persona that reviews code (engineer, QA, EM, end to end, and a
designer or researcher who said they write code), on a local host: if `command -v px0` fails, **offer**
to install it as its own, separate go-ahead (never bundled with the second family), saying in one
sentence what it does (every harness PR gets a px0 review link in its own worktree, doc 20 §8f) and
that Security should sign off on first use because it is an external tool not yet in Apollo's approved
tool directory (point them at #security-requests). **Before offering, read `framework/models/px0-pin.yml`:
if `version` is `"0.0.0"` or `sha256` is the all-zero placeholder, do not offer the install at all —
say "px0 install unavailable: pin file at `framework/models/px0-pin.yml` is placeholder, pending
Security sign-off", record `tools.px0: n/a-pending-pin` in the profile, and move on.** On "yes" with a
real pin, prefer Homebrew: `brew install px0` (if the tap is available) and confirm with
`px0 -version`. If no Homebrew tap is reachable, pin the install: fetch the script to disk, verify its
SHA-256 against the version pinned in `framework/models/px0-pin.yml` (`PX0_VERSION` and `PX0_SHA256`),
and only then execute it:

```bash
set -euo pipefail
PX0_VERSION=$(python3 -c "import yaml,sys; print(yaml.safe_load(open('${CLAUDE_PLUGIN_ROOT}/framework/models/px0-pin.yml'))['version'])")
PX0_SHA256=$(python3 -c "import yaml,sys; print(yaml.safe_load(open('${CLAUDE_PLUGIN_ROOT}/framework/models/px0-pin.yml'))['sha256'])")
tmp=$(mktemp -d)
curl -fsSL "https://px0.ai/install/${PX0_VERSION}/install.sh" -o "$tmp/install.sh"
echo "${PX0_SHA256}  $tmp/install.sh" | shasum -a 256 -c -
VERSION="$PX0_VERSION" sh "$tmp/install.sh"
PX0_REPORTED_VERSION=$(px0 -version | awk '{for (i = 1; i <= NF; i++) if ($i ~ /^v?[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.]+)?$/) {sub(/^v/, "", $i); print $i; exit}}')
[ "$PX0_REPORTED_VERSION" = "${PX0_VERSION#v}" ] || {
  echo "px0 version mismatch: expected $PX0_VERSION, got $PX0_REPORTED_VERSION" >&2
  exit 1
}
```

Refuse to install on a checksum mismatch or reported-version mismatch and report it to the person; never fall back to the unpinned
`curl ... | sh` form. A Homebrew install runs the same `PX0_REPORTED_VERSION` equality check against
the pin and aborts on a mismatch. If `px0 -version` reports a newer version available, update through the same
verified path: for a Homebrew install, `brew upgrade px0`; for a pinned install, bump `px0-pin.yml`
to the new version and SHA-256 (Security sign-off again when the bump crosses a major release), then
re-run the verified fetch above. The in-place `px0 --update` command is never used, because it would
replace the binary without re-checking the pinned SHA-256. Record `tools.px0: <version>` in the
profile, or `declined <date>`, or `n/a-cloud` on a cloud host.
Never install it for a designer or UX persona who does not write code.

When the selected tracker is Jira or both, Atlassian is required even if the persona table would not
otherwise require it. Confirm it with `atlassianUserInfo` as doc 39 says. If it is missing, give the doc 39
setup command and login step, retain the selected `updates.tracker`, write `updates.tracker_blocked: jira`,
and use Notion for updates until a harmless Atlassian call succeeds. Do not block onboarding.

**Second family (when question 7 is yes), Claude Code host:** run and confirm each line:
Default for every non-design persona (question 7): first the Codex plugin, then `/apollo-product-lab:harness-shunt setup` (it runs `codex login`, installs shunt, writes the route into `~/.claude/settings.json` so the Desktop Code tab is covered too, and proves the route with one gpt-6-astra reply). Run them; do not offer them as optional. By hand: `codex login` → `brew install pleaseai/tap/shunt` → `cp ${CLAUDE_PLUGIN_ROOT}/framework/models/shunt.toml.example ~/.config/shunt/shunt.toml`
→ `brew services start shunt` → `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3001/` must print 200
→ tell them to `export ANTHROPIC_BASE_URL=http://127.0.0.1:3001` in the shell that launches `claude`, and
that the session-start line will say "routed through shunt" once it is. Codex host: `npm i -g @anthropic-ai/claude-code` and `claude login`; lenses run as detached `claude -p` calls.

Only the rows doc 39 marks for this persona. For each gap give the exact command or click path from doc 39 and wait; say what is optional. For an MCP server that is neither shipped nor present: `claude mcp add --transport http <name> <url>` with the URL from doc 39, then the login on first call. Confirm each one by calling one harmless tool (Notion `search`, Atlassian `atlassianUserInfo`, Slack `slack_search_channels`, Glean `search`, Figma `whoami`, Claude Design `list_projects`, Sentry the org tool, Amplitude `get_amplitude_context`, Grafana `list_datasources`, Playwright `browser_navigate` to the preview) and report `present` only after the call succeeds. Designers: Fabric Studio (offer `/apollo-rnd:setup-fabric-studio`, which installs Node 22, gh and the clone) and Figma first. PMs: Notion, Glean, Amplitude, Enterpret; point them at `/apollo-product:product-overview` once and `/apollo-rnd:prd-one-pager` for Stage C. Engineers: gh, docker, Codex, shunt. QA: Playwright, Sentry, the preview URL. Never ask for a secret in chat; say where it goes instead.

## 4. Write the profile

Carry over any existing `approvals:` block untouched; never invent one. If the persona asks for Gemini or DeepSeek, say plainly: Gemini is available only through Glean for the internal record and DeepSeek has no lane (doc 37 §3); do not describe any other setup.

Fill `templates/harness-profile.yml`, including `surface:` and `storage:` from question 0. Where the profile goes depends on `profile_store` (doc 45 §4):

- `local`: write it to `~/.claude/harness-profile.yml` (Bash heredoc).
- `notion` (claude.ai/code, claude.ai chat, or no writable home): find the person's id with `notion-get-self` (or `notion-get-users` with `user_id: "self"`, whichever this session advertises), then `notion-search` "Harness profile" and keep pages created by that user whose body has `record_key: harness-profile.yml`. The profile is the one record that is **updated in place**, not superseded: if one page exists, replace its content with `notion-update-page` `replace_content`; if several exist, use the most recently edited, say which, and offer to trash the others. If none exists, run `storage.py profile-to-notion <filled file> --name <name>` and make the printed `notion-create-pages` call (it uses `creation_mode: "draft"` with no parent, so the page is private; Notion refuses a parent with draft mode). With no code execution, build the body by hand per doc 45 §3.1 (plain text, `sha256: unavailable (no code execution)`). Never put the profile under `notion_parent` or the records root. Also create the records root `Harness record: <initiative>` under `notion_parent` for each initiative in notion mode, and write its URL as `notion_records_root` in the profile. Every later session on that surface reads the profile with one search.

Show the person the file. It contains no secrets.

Prepare one onboarding ledger event. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/post-update.py" --stage RUN.onboard --summary "Harness onboarding completed" --links "" --initiative <initiative> --run <run-id> --event <stage-event-id> --agent skill:harness-onboard --outcome <stage-outcome> --profile <profile>`. The ledger write depends on the detected storage mode:

- **`storage: local`:** append the event to `.ai/<initiative>/ledger.jsonl` with `framework/ledger/append.py` exactly once. Then execute every call in the update plan. When updates include Notion, the plan's `storage.py ledger-entry` call posts the same event to Notion; it does not replace or repeat the canonical local append. Do not run `append.py` again.
- **`storage: notion`:** do not run `append.py`. Execute every call in the update plan, including any Jira comment; the plan's `storage.py ledger-entry` call runs exactly once. If the plan has no ledger call because updates are Jira-only, run `storage.py ledger-entry` once against the latest fetched ledger page after the Jira update. Never execute more than one Notion ledger append for the event.

A Jira-only selection with `tracker_blocked: jira` uses the Notion fallback recorded in the plan.

## 4b. Point them at the initiative

- Existing initiative: run `/harness-snapshot read <initiative> <run>` now and show the three most important rows.
- New initiative: say that `/product-harness-init <slug>` is the next command and what it will ask for (PRD, estimate, constraint register, design artifact, tracker epic; "not found" is a valid answer). Do not run it from here.
- Feature in an existing initiative: `/product-harness-init <initiative> --feature <slug> "<one-line ask>"`.
- Change to an existing Apollo product with no harness folder: `/harness-intake "<one-line ask>"`; it writes the current behaviour map and owners as the first snapshot (doc 43 §7).
- A different repo than leadgenie: the same commands work; the product repo needs a `.ai/` directory and, for a team, the git rules in doc 41.

## 4c. Ask for the statement, then hand to intake

Ask: *"In one sentence, what do you want to do?"* Then run `/harness-intake "<their sentence>"` (skill in
this plugin). Intake sizes the work, lists the artifacts that exist and those that are missing, adds the
feature-specific connectors, names the compliance checks, and proposes the ordered next steps for their
persona. They confirm once; the first deterministic stage runs. Nobody has to know the stage names.

## 5. Show their flow, then the sync point

For designers, say plainly: you share Figma, Fabric Studio prototypes or Claude Design projects, and the harness never asks you for a PR or a staging link. Snapshots and Notion pages are written only inside a harness run (a run id
is bound and the work is a harness stage, such as a design council). Ordinary Figma edits and storyboard
updates write nothing and publish nothing.

Print, for their persona, from doc 36: the first command, what comes back, the gate they own, and where the record lives (`.ai/<initiative>/runs/<run>/`). Then the one sentence that applies to everyone: *decisions arrive as options with a recommendation; you choose; if you ever get an open question instead, that is a harness defect, say so.*

If they are joining an initiative that already has runs, finish by running `/harness-snapshot read <initiative> <run>` for them so they start from the record, not from a conversation.

Also show the persona's rows from `${CLAUDE_PLUGIN_ROOT}/framework/38-skill-reuse-map.md` (the skills they already have) and which plugins from doc 39 §Plugins are missing on this host (`claude plugin list`).

## Updating a zip install

A plugin uploaded as a zip (Claude Desktop, claude.ai) does not update itself. The session-start line
prints the loaded version and build, for example `[apollo-product-lab 1.0.0 build 07d1aeb]`. To update:
build the zip from the latest `akansh/harness-split-1` branch (or `main` once merged) with the commands in
the plugin README (they write a `BUILD` file with the commit), replace the uploaded plugin under
Customize, Plugins, and restart Claude Desktop. The new version shows on the next
session-start line.

## Hard rules

- Detect, do not assume. If you cannot detect a connector, say `unknown`, never `present`; a connector is `present` only after a confirmed call.
- The person picks a role and gives a statement. The framework decides which artifacts to produce (intake), never the person.
- Never paste or request tokens, keys, or callback URLs with codes.
- Do not create agents, initiatives, or runs here; point to `/product-harness-init`.
- Keep it under ten minutes of the person's time; the docs exist for later.
