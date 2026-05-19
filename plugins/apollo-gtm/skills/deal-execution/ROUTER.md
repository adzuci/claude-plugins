---
name: apollo-gtm-router
description: >
  Lightweight entry point for the Apollo GTM System. Reads the task, selects
  the execution path, and loads ONLY the files needed. This file replaces
  SKILL.md as the first file read on any request. Always load this.
  Never load SKILL.md at runtime (it is the full architecture reference).
  For first-time setup or troubleshooting, read PREFLIGHT.md instead.
metadata:
  version: '1.1'
  token_cost: ~900
---

# Apollo GTM Router

Read this file first on every request. It tells you what to load and what NOT to load.

## Session Start

On every new session, before processing any task:

0. **Load local config.** Mount `~/Documents` via `request_cowork_directory` if not already mounted. Read `~/Documents/apollo-gtm/config.yaml`. If the file exists, store all values in session state — identity, triage_config, connectors, and state flags. These values are used by every downstream path. If the file does not exist, the AE has not run preflight yet — proceed to step 1 (preflight will create it). See `utilities/local-config.md` for schema and read protocol.

1. **Check if preflight is needed.** If the user says "setup," "install," "preflight," "verify connections," or "check setup," load `PREFLIGHT.md` and run the setup flow. Do not proceed with this file until preflight passes. Also load preflight if step 0 found no config file.

2. **Check if onboarding is needed.** If `state.onboarding_complete` is `false` or missing in the local config:
   - If the user provides a direct task (e.g., "run my triage," pastes an email thread, asks a deal question), set `onboarding_complete: true` and proceed to Step 1: Classify the Task. The user's explicit intent overrides onboarding.
   - If the user asks for help ("help," "how do I...," "what does X do"), load `ONBOARDING.md` help section and respond to their question. Then present the action menu. Do not run the walkthrough for specific help requests.
   - Otherwise, load `ONBOARDING.md` and run the first-run walkthrough.

3. **If the user asks for help** ("help," "how do I...," "what does X do," "explain..."), load `ONBOARDING.md` help section and respond to their question. Then present the action menu.

4. **If the user provides a task directly** (e.g., "run my triage," pastes an email thread, asks a deal question), skip the menu and go straight to Step 1: Classify the Task.

5. **If the user opens the session without a specific task** (e.g., loads the skill, says "hello," "what can I do," or gives no clear instruction), present the action menu:

**Instruction to model:** Use `AskUserQuestion` with the following:

```
Question: "What would you like to do?"
Header: "Action"
Options:
  - Label: "Run inbox triage"
    Description: "Process your unread email, check calendar and Slack context, draft replies, and deliver a summary to your Slack DM."
  - Label: "Process an email thread"
    Description: "Paste a sales email thread and get a drafted reply grounded in the deal context."
  - Label: "Write a call follow-up"
    Description: "Paste a call transcript or notes and get a follow-up email tied to what was discussed."
  - Label: "Review a deal"
    Description: "Name a deal and get stage validation, MEDDPICC gap analysis, and recommended next actions."
```

**After selection:**
- "Run inbox triage" → Path A
- "Process an email thread" → Path B. Prompt: "Paste the email thread here."
- "Write a call follow-up" → Path C. Prompt: "Paste your call transcript, notes, or recording summary."
- "Review a deal" → Path D. Prompt: "Which deal?"
- User selects "Other" or types free text → Classify using Step 1 below.

## Step 1: Classify the Task

| If the task is... | Go to |
|---|---|
| "Run my AM/PM triage" or "triage my inbox" | **Path A: Inbox Triage** |
| User pastes an email thread and wants a reply | **Path B: GEN-SE** |
| "Write a follow-up for this call" + transcript/notes | **Path C: Follow-Up Engine** |
| Deal question, stage check, MEDDPICC gap, call prep | **Path D: GTM Reference** |
| Pasted text that needs analysis (not sales email) | **Path E: Pipeline Analysis** |
| Data test / enrichment prep | **Path F: Utility** |
| Task management | **Path G: Utility** |
| Technical feasibility check | **Path D: GTM Reference** |
| Help request, system question, "how do I..." | **Path H: Help** |
| "Change settings," "adjust triage," "change my email" | **Path I: Settings Change** |
| "Post to Slack" / "Draft an email" / execution action | Read `references/functions.md` (~1.5K tok) then execute |

## Step 2: Load the Path

### Path A: Inbox Triage (~18-30K tokens per-thread)

LOAD: `orchestrators/inbox-triage.md`
LOAD: `orchestrators/references/classification-gate.md`
LOAD: `orchestrators/references/hard-rules.md`
LOAD: `orchestrators/references/summary-format.md`
LOAD: `references/functions.md`

The orchestrator controls per-thread file loading. It loads `gense/gense.md` for sales threads and the full pipeline specs (L1-L4+) for non-sales threads. This is correct — inbox triage is the highest-stakes path and benefits from the full reasoning discipline at each layer. Do NOT override the orchestrator's load instructions. Do NOT load files upfront — the orchestrator loads per-thread after classification.

### Path B: GEN-SE (single thread) (~5K tokens)

LOAD: `gense/gense-runtime.md`

The runtime file contains the complete action table, FOUNDATION 10→24 mapping, ThreadState schema, and all execution logic. Only load the full `gense/gense.md` if the runtime file is insufficient (complex edge case, architecture question, or debugging a prior run).

### Path C: Follow-Up Engine (~8K tokens)

LOAD: `orchestrators/followup-engine.md`
LOAD: `orchestrators/references/call-state-extractor.md`
LOAD: `references/methodology.md` (for CoTM framework — Before/After, PBOs, Required Capabilities)

### Path D: GTM Reference (~2-6K tokens)

Load ONLY the relevant reference file(s):

| Question about... | Load |
|---|---|
| Discovery, value conversation, objection handling | `references/methodology.md` (~1.6K) |
| Deal stage, SFDC fields, exit criteria | `references/sales-process.md` (~2K) |
| MEDDPICC fields, champion testing, scoring | `references/meddpicc.md` (~1.8K) |
| Cross-framework validation | `references/framework-linkages.md` (~1.7K) |
| Technical feasibility, CRM compatibility | `references/technical-requirements.md` (~1.1K) |
| Competitive positioning | `references/business-context.md` (~0.7K) |
| Product capabilities | `references/product-one-sheets/` (relevant file, ~0.7K each) |
| SFDC Capabilities field | `references/capabilities-definitions.md` (~1K) |

Do NOT load pipeline skills for reference questions. Just read the reference and answer.

**Notion augmentation (optional):** If Notion MCP is connected and the question involves a specific deal, account, or competitor, search Notion for deal pages, battlecards, or enablement content to augment the reference answer. See `references/functions.md` Notion section for tool names and query patterns. Notion content is `self_report` quality — attribute it, don't treat it as authoritative.

### Path E: Pipeline Analysis (~8K tokens)

LOAD: `pipeline/pipeline-runtime.md`

This is the consolidated runtime for L1 through L4+. Only load individual full pipeline skills if the runtime is insufficient (debugging, architecture discussion, or extending behavior).

### Path F/G: Utility

- Data test: Load `utilities/apollo-data-test-runner.md` (~7K tok)
- Task tracker: Load `utilities/task-tracker.md` (~7K tok)

### Path H: Help (~3K tokens)

LOAD: `ONBOARDING.md` (help section only)

Match the AE's question to the closest help topic and respond. After responding, present the action menu. Do NOT load pipeline or GEN-SE files for help requests.

### Path I: Settings Change (~1K tokens)

LOAD: `utilities/local-config.md` (schema reference)

The AE wants to change a setting. Read the current config from session state (loaded in Step 0). Based on what they want to change:

- **Identity** (email, domains, Slack ID): Run `PREFLIGHT.md` auto-detection routine for just the requested field. Write updated value to local config.
- **Triage preferences** (mode, thread limit, time window, priority): Present the same triage preference options from `PREFLIGHT.md` Triage Preferences section. Write updated values to local config.
- **Other / unclear**: Ask what they want to change. Show current values from the config.

After writing, confirm: "Updated. This will take effect on your next triage run."

## Rules

1. **Never load all files.** The full system is ~187K tokens. No task needs more than ~20K of instruction.
2. **Two-tier loading.** Orchestrators (Path A, C) load full specs for multi-layer reasoning. Direct paths (Path B, E) load runtime files for efficiency. Only escalate from runtime to full spec when the runtime is insufficient (complex edge case, debugging, or architecture review).
3. **FOUNDATION.md is architecture documentation.** Do not load at runtime. All runtime-critical content (tag set mapping, constraint severity, action space mapping) has been inlined into `pipeline/pipeline-runtime.md` and `gense/gense-runtime.md`. FOUNDATION.md exists in `docs/archive/` for architecture review only.
4. **Reference files are small.** Load them freely when the task touches GTM methodology.
5. **GEN-SE modules (execution-spine/) are never loaded at runtime.** The runtime file covers execution. The modules are for architecture review and debugging only.
6. **Present the action menu** when the user opens a session without a clear task. Do not wait for them to guess what to type.
