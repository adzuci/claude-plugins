---
name: task-tracker
description: >-
  Persistent operational utility that manages a local task file as a battlefield map
  of active work. Accepts messy, compound, high-context input and decomposes it into
  structured, workstream-grouped, constraint-classified task entries. Designed for an
  operator who thinks in workstreams and parallel fronts, not atomic checklists.
  Classifies work by operational mode (threat, hunt, build, farm, admin, quick-win),
  tracks status independently (open, in_progress, blocked, waiting, done, dropped),
  preserves re-entry context so parallel threads can be resumed without full
  reconstruction, detects leverage points and stale loops, and emits constraint
  material to the pipeline. Use when the user dumps raw material and expects structured
  capture, asks for a board review, says "what's on my plate" or "what am I forgetting,"
  pastes emails/notes/threads for action extraction, or needs to re-enter a stalled
  workstream.
metadata:
  author: David Johnson-Hall
  version: '2.3'
  layer: utility-persistent-state
  architecture: Apollo GTM Skill Library
  changelog: >-
    v2.3 patch (2026-04-15): Directory consolidation.
    [1] Task directory moved from ~/Documents/tasks/ to ~/Documents/apollo-gtm/tasks/
    for co-location with system config file (config.yaml).
    [2] Added migration logic: move existing files, leave symlink at old path.
    [3] Added reference to sibling config file (utilities/local-config.md).
    ---
    v2.2 patch (2026-03-26): Cowork persistence fix.
    [1] Changed default task file from ~/Desktop/tasks.yaml to ~/Documents/tasks/tasks.yaml.
    [2] Replaced ~/.task-tracker-config.yaml (sandbox home resets between Cowork
    sessions) with CLAUDE.md as the durable config mechanism.
    [3] Added Cowork environment handling: mount ~/Documents via
    request_cowork_directory before any file I/O.
    [4] Updated archive default to ~/Documents/tasks/tasks-archive.yaml.
    ---
    v2.1 patch (2026-03-26): 8 changes from architectural audit.
    [1] Removed blocked/waiting from mode enum; they are now status-only values.
    Mode describes the work type, status describes the current state.
    [2] Added structured convention to reentry_context for consistency.
    [3] Added optional effort field (S/M/L/XL) to task schema.
    [4] Added optional parent_id field for subtask linkage.
    [5] Clarified farm detection scope and mechanism.
    [6] Added config file for persistent file location across sessions.
    [7] Specified archive mechanics: trigger, format, lifecycle.
    [8] Added known gap: no version history/undo. Recommends git sync.
---

# Task Tracker

Persistent operational utility. Manages a local task file as a battlefield map, not a checklist. Captures chaos, preserves context, exposes constraints, shows threat and leverage, and makes re-entry brutally easy.

## Purpose

task-tracker exists because the operator's real failure mode is not forgetting that tasks exist. It is losing closure, re-entry context, and sustained follow-through across parallel fronts. The same open loop gets re-discovered, re-analyzed, and re-forgotten across sessions, not because it was never captured, but because it was captured without enough context to act on later.

task-tracker solves five problems:

1. **Capture decay.** Tasks surface in emails, meetings, Slack, brain dumps, pasted threads, and pipeline output. Without structured capture, they degrade into "I think there was something."
2. **Re-entry cost.** The operator runs many parallel fronts. Returning to a stalled workstream currently requires full context reconstruction ("zoom out, pull everything, rebuild the model"). The task file must preserve enough state to make re-entry cheap.
3. **Constraint blindness.** Active tasks with deadlines, blockers, dependencies, and capacity implications are constraint material. If they are invisible to the pipeline, constraint-first-reasoner maps an incomplete landscape.
4. **Leverage invisibility.** Not all tasks are equal. Some unblock multiple downstream outcomes. Without explicit leverage classification, high-impact moves get buried under admin noise.
5. **Pattern blindness.** Recurring task shapes (follow-up loops, admin maintenance, repeated extraction) should become automation candidates, not permanent manual entries.

## When to Use This Skill

Use task-tracker whenever:
- The user dumps raw material (email, meeting notes, Slack, brain dump, screenshot, voice memo, conversation log) and expects structured capture
- The user asks "what's on my plate," "what am I forgetting," "what needs to happen," "what's stale," or any board-review variant
- The user needs to re-enter a workstream after a pause and wants current state
- state-extractor output contains `open_loops` or `requests` with `status: open` that represent persistent action items
- A pipeline run surfaces tasks that should survive beyond the current conversation
- The user asks for triage: "what should I focus on," "what's the minimum move," "what's blocked"
- The user wants to understand their operational constraint landscape from a workload perspective

## When NOT to Use This Skill

- The open loop is ephemeral and conversation-scoped (e.g., "reply to this message" during active drafting). Not every open_loop is a persistent task.
- The user is asking for project planning, roadmap construction, or strategic architecture. task-tracker manages operational tasks, not plans.
- The task belongs in an external system (Jira, Linear, Notion database) and the user has said so.
- The input is a single atomic instruction with no tracking dimension ("send this email"). Execute it; don't track it.
- The user is doing pure creative or exploratory work with no action output.

## Core Principles

1. **Accept chaos, emit structure.** The user will not enter pristine to-dos. The skill must ingest brain dumps, pasted threads, compound requests, screenshots, and half-formed workstream descriptions and decompose them. If capture requires effort, it will not happen.
2. **Workstreams are the natural unit.** Tasks are grouped by workstream (Apollo, JHD, legal, skill-library, personal, etc.). A task without a workstream is orphaned context. Workstreams are the re-entry handles.
3. **Mode is the work type. Status is the current state.** Mode describes what kind of energy and approach a task requires (threat, hunt, build, farm, admin, quick-win). Status describes where it sits right now (open, in_progress, blocked, waiting, done, dropped). These are orthogonal. A `mode: build` task can be `status: blocked`. A `mode: hunt` task can be `status: waiting`. Mode does not change when a task gets stuck; status does. [CHANGED v2.1: resolved mode/status collision. `blocked` and `waiting` removed from mode enum; they exist only as status values.]
4. **Re-entry is the killer feature.** Each workstream carries a `reentry_context` field with a structured convention: last action, current state, next move, blocker if any. This is what makes the difference between "I need to rebuild the whole picture" and "I know exactly where I left off." [CHANGED v2.1: added structured convention to reentry_context.]
5. **Constraints propagate.** Tasks with deadlines, blockers, or capacity implications are constraint material. The pipeline reads them.
6. **Leverage over urgency.** Triage surfaces the move that unlocks the most downstream outcomes, not just the most overdue item.
7. **Detect patterns, suggest farming.** When the same task shape appears 3+ times within the active task file or archive (when loaded), flag it as an automation candidate. Farm detection is triggered during triage and deep review, not automatic across sessions. The `recurrence_pattern` field is the manual override for operator-spotted patterns. [CHANGED v2.1: clarified farm detection scope and mechanism.]
8. **Staleness is signal.** A task untouched for 14+ days is information. A workstream untouched for 14+ days is a stronger signal.
9. **Status honesty.** `done` means the action was performed. `dropped` means it was deliberately abandoned with a reason. No someday/maybe. No guilt storage.
10. **Minimum maintenance.** The system must survive uneven rhythms, spiky workloads, multi-domain bursts, quiet stretches. Heavy grooming kills adoption.

## Relationship to the Pipeline

task-tracker is not a pipeline layer. It is an operational utility that connects at two integration points.

### Inbound: Pipeline to Task File

When state-extractor produces `open_loops` or open `requests`, those are task candidates. The capture process evaluates each against qualifying criteria:
- Is this a persistent action (survives beyond the conversation)?
- Is there an identifiable owner?
- Is this already in the file (semantic dedup)?
- Does this map to an existing workstream?

Pipeline-captured tasks are always presented for confirmation before writing.

### Outbound: Task File to Pipeline

When constraint-first-reasoner runs, active tasks feed its constraint landscape:
- Tasks with approaching `due_date` -> `timing_window` constraints
- Tasks with `status: blocked` -> `dependency` constraints
- Tasks with `mode: threat` -> elevated severity
- Total active effort relative to capacity -> `resource_cap` constraints (uses `effort` field when available, falls back to task count) [CHANGED v2.1: effort-aware capacity math]
- Overdue tasks -> `timing_window` with `immediacy: active_now`
- Stale workstreams -> `environmental_constraint` (context decay risk)
- Tasks with `status: waiting` -> `dependency` constraints with `depends_on` surfaced [CHANGED v2.1: waiting now emits via status, not mode]

## Task File Specification

### File Location and Configuration

Default: `~/Documents/apollo-gtm/tasks/tasks.yaml`

The task file and archive live on the operator's local Mac filesystem so they persist between Cowork sessions. The Cowork sandbox resets on every session, so nothing stored in the sandbox home directory (`~` inside the VM) survives. The durable config mechanism is CLAUDE.md, which lives on the Mac at `~/.claude/CLAUDE.md` and is loaded into every session automatically.

**Directory structure:** The task file lives under the shared `~/Documents/apollo-gtm/` directory alongside the system config file (`config.yaml`). See `utilities/local-config.md` for the full directory layout. The task file and config file are independent — they share a parent directory but have separate read/write lifecycles.

[CHANGED v2.3: task directory moved from ~/Documents/tasks/ to ~/Documents/apollo-gtm/tasks/ for co-location with system config. Migration: if old path exists and new path doesn't, move files and leave a symlink.]

**Cowork environment setup (required before any file I/O):**

The task file lives on the Mac at `~/Documents/apollo-gtm/tasks/tasks.yaml`. In the Cowork sandbox, this maps to the mounted path after running `request_cowork_directory` with `path: ~/Documents`. This mount step must happen before any read or write. If the directory is already mounted (check by testing if the mount path exists), skip the mount request.

```
# Effective paths
Task file (Mac):    ~/Documents/apollo-gtm/tasks/tasks.yaml
Task file (VM):     /sessions/<session-id>/mnt/Documents/apollo-gtm/tasks/tasks.yaml
Archive file (Mac): ~/Documents/apollo-gtm/tasks/tasks-archive.yaml
Archive file (VM):  /sessions/<session-id>/mnt/Documents/apollo-gtm/tasks/tasks-archive.yaml
Config file (Mac):  ~/Documents/apollo-gtm/config.yaml  (managed by local-config.md, not this skill)
```

**Resolution order on load:**
1. Mount `~/Documents` via `request_cowork_directory` if not already mounted.
2. Check CLAUDE.md for a `Task Tracker Persistence` section with an explicit path override. If present, use that path.
3. If no CLAUDE.md override, use default: `~/Documents/apollo-gtm/tasks/tasks.yaml`.
4. Migration: if `~/Documents/tasks/tasks.yaml` exists and `~/Documents/apollo-gtm/tasks/` does not, move files to the new location and leave a symlink at the old path.
4. If the file does not exist at the resolved path, create it with the empty schema.
5. Do not use `~/.task-tracker-config.yaml`. It lives in the sandbox home directory and does not persist between sessions.

### File Schema

```yaml
# JHD Task Tracker - Operational Battlefield Map
# Last updated: {ISO 8601 timestamp}
# Owner: David Johnson-Hall

meta:
  version: 2.2
  last_reviewed: {ISO 8601 date}
  last_updated: {ISO 8601 timestamp}
  active_count: {int}  # open + in_progress + blocked + waiting
  total_count: {int}

workstreams:
  - name: {string}  # e.g., "apollo", "jhd", "legal", "skill-library", "personal"
    status: active | paused | closed
    reentry_context:
      last_action: {string - what was done most recently}
      current_state: {string - where things stand right now}
      next_move: {string - the next concrete action}
      blocker: {string | null - what is preventing progress, if anything}
    last_activity: {ISO 8601 date}
    task_count: {int}

tasks:
  - id: {sequential int, never reused}
    task: {string - verb-first atomic action}
    workstream: {string - must match a workstream name}
    status: open | in_progress | blocked | waiting | done | dropped
    mode: threat | hunt | build | farm | admin | quick-win
    effort: {S | M | L | XL | null}
    created: {ISO 8601 date}
    due_date: {ISO 8601 date | null}
    context: {string - provenance: "email from Sarah 3/15", "standup 3/26", "brain dump"}
    owner: {string - default "me"}
    blocker: {string | null - what is preventing progress, required when status is blocked}
    depends_on: {string | null - external person, event, or condition this waits on, required when status is waiting}
    leverage: {string | null - what downstream outcomes this unblocks, if known}
    parent_id: {int | null - links to parent task id when this task was decomposed from a larger item}
    tags: [{string}]
    notes: {string | null}
    completed_date: {ISO 8601 date | null}
    dropped_reason: {string | null}
    last_touched: {ISO 8601 date}
    recurrence_pattern: {string | null - if this task shape repeats, describe the pattern}
```

**Schema changes from v2.0:**
- `status` enum: added `waiting` (was previously a mode). [PATCH 1]
- `mode` enum: removed `blocked` and `waiting` (now status-only). [PATCH 1]
- `reentry_context`: changed from free-text string to structured map with four fields. [PATCH 2]
- `effort`: new optional field. T-shirt size for capacity reasoning. [PATCH 3]
- `parent_id`: new optional field. Links decomposed subtasks to their parent. [PATCH 4]
- `depends_on`: now required when `status: waiting` (was advisory only). [PATCH 1]
- `meta.active_count`: now includes `waiting` status in the count. [PATCH 1]

### Operational Mode Definitions

Mode describes the type of work, not the current state. A task's mode should remain stable even when its status changes. A `mode: hunt` task that gets stuck becomes `status: blocked, mode: hunt`, not `mode: blocked`. [CHANGED v2.1]

| Mode | Definition | Triage Behavior |
|---|---|---|
| threat | Immediate risk: legal, financial, career, relationship, reputation. External consequences if not handled. | Surface first. Always. |
| hunt | High-energy, high-leverage, identity-aligned work. The operator wants to do this. | Make visible and easy to attack. Do not bury under admin. |
| build | Strategic system-building. Compounding upside but no immediate deadline. | Track progress. Flag when stale. |
| farm | Recurring pattern that should become an automation, template, or delegation. | Flag for automation conversion after 3+ occurrences. |
| admin | Low-energy maintenance, bureaucratic, or repetitive work. Annoying but necessary. | Batch together. Do not let it crowd out hunt/build work. |
| quick-win | Can be done in <15 minutes and clears mental load. | Surface during review as easy momentum items. |

### Status Definitions

Status describes the current state of the task. Status changes; mode usually does not. [NEW v2.1]

| Status | Definition | Required Fields |
|---|---|---|
| open | Not yet started. Available to work. | (none beyond base) |
| in_progress | Actively being worked on. | (none beyond base) |
| blocked | Cannot proceed. Waiting on a specific condition or resolution. | `blocker` required. |
| waiting | Depends on another person's action or response. Not stuck, but paused pending external input. | `depends_on` required. |
| done | Action was performed. Terminal state. | `completed_date` required. |
| dropped | Deliberately abandoned. Terminal state. | `dropped_reason` required. |

**Status transitions:**
- `open` -> `in_progress` -> `done`
- any -> `blocked` (with `blocker`)
- any -> `waiting` (with `depends_on`)
- `blocked` -> `in_progress` (blocker resolved)
- `waiting` -> `in_progress` (dependency satisfied)
- any -> `dropped` (with `dropped_reason`)
- No backward from `done`. No backward from `dropped`.

### Effort Sizing

Optional field. When present, enables effort-aware capacity reasoning in triage. When absent, triage falls back to task count. [NEW v2.1]

| Size | Definition | Approximate Scope |
|---|---|---|
| S | Trivially small. No deep thinking. | < 30 minutes |
| M | Meaningful but bounded. Clear scope. | 30 min to 2 hours |
| L | Substantial. May need a focused block. | 2 to 8 hours |
| XL | Multi-session or multi-day. May need decomposition. | > 8 hours |

Rules:
- Default: null. Do not require effort on capture. The operator or triage sets it.
- If `effort: XL` and no `parent_id` children exist, triage should flag: "This is XL with no subtasks. Consider decomposing."
- Effort is an estimate, not a commitment. Do not track actuals.

### Parent/Subtask Linkage

Optional. Used only when a task has been decomposed from a larger item. [NEW v2.1]

Rules:
- `parent_id` is null by default. Only populated on decomposition.
- Parent tasks are not required to exist. If a parent is marked `done` or `dropped`, orphaned children surface in triage as "orphaned subtasks."
- Triage can roll up: "Task #12: 3/5 subtasks done."
- Do not create hierarchy for its own sake. Most tasks should have `parent_id: null`. Decompose only when a task is genuinely compound and tracking the parts separately adds value.
- Maximum depth: 1. No sub-sub-tasks. If a subtask needs further decomposition, it becomes a peer with a shared parent.

### Schema Rules

- `id` is sequential, never reused. Gaps expected.
- `task` always starts with a verb.
- `workstream` is required. If a task does not fit an existing workstream, create one.
- `mode` defaults to `admin` on capture. The operator or triage adjusts it. Conservative default prevents mode inflation.
- `mode` describes work type and should not change when a task gets stuck or paused. Change `status`, not `mode`. [CHANGED v2.1]
- `status` transitions are defined above. `blocked` requires `blocker`. `waiting` requires `depends_on`. `done` requires `completed_date`. `dropped` requires `dropped_reason`. [CHANGED v2.1]
- `due_date` is null when no deadline exists. Never invent deadlines.
- `context` is required. Provenance is the audit trail.
- `effort` is null by default. Set when known. Do not guess.
- `parent_id` is null by default. Set only on decomposition. [NEW v2.1]
- `leverage` captures downstream unlocks when identifiable. Not required on every task.
- `recurrence_pattern` is set when the operator or triage detects this task shape has appeared before.
- `last_touched` updates on any modification.
- Completed tasks remain in the active file until archived during deep review. See Archive Mechanics. [CHANGED v2.1]
- `reentry_context` on the workstream updates whenever any task in that workstream changes. All four subfields must be current. This is the single most important field for the operator's workflow. [CHANGED v2.1]

## Process

### Step 1: Load Task File

**Resolution order:**
1. Mount `~/Documents` via `request_cowork_directory` if not already mounted.
2. Check CLAUDE.md for an explicit path override in the `Task Tracker Persistence` section.
3. If no override, use default: `~/Documents/tasks/tasks.yaml`.
4. If file does not exist, create with empty schema.

Read from resolved path. Validate structure. Report malformed entries without silently dropping.

**If corrupted:** Stop. Show what is wrong. Do not overwrite without explicit permission.

**Migration (v2.1 to v2.2):** If a loaded file has `meta.version: 2.1`: no schema changes. Set `meta.version: 2.2`. The only changes are to file location and config resolution, not to the task data itself.

**Migration (v2.0 to v2.1):** If a loaded file has `meta.version: 2`:
- Convert any tasks with `mode: blocked` to `status: blocked, mode: admin` (conservative; operator adjusts mode).
- Convert any tasks with `mode: waiting` to `status: waiting, mode: admin` (conservative; operator adjusts mode).
- Convert `reentry_context` free-text strings to structured format by best-effort parsing into the four subfields.
- Add `effort: null` and `parent_id: null` to all existing tasks.
- Set `meta.version: 2.1`.
- Present migration summary to operator for confirmation before writing.

### Step 2: Ingest and Decompose

This is the primary capture step. It must handle the operator's actual input patterns.

**Input types accepted:**
- Direct task statement ("add: email Sarah the deck by Friday")
- Compound statement ("email Sarah, update the CRM, schedule the follow-up")
- Brain dump (unstructured stream of consciousness)
- Pasted email thread
- Pasted meeting notes
- Pasted Slack thread
- Pasted document excerpt
- Pipeline output (state-extractor open_loops)
- Verbal/casual reference ("I told Drew I'd handle the contract thing")

**Decomposition protocol:**

1. **Parse for actionable items.** Scan for: commitments made, requests directed at the operator, decisions requiring execution, open loops that will decay, dependencies blocking progress, deadlines mentioned.
2. **Decompose compounds.** Separate statement into atomic tasks. One verb, one owner, one action per task. If the compound represents a single larger effort with distinct parts, use `parent_id` linkage: create a parent task and link the subtasks. [CHANGED v2.1]
3. **Assign workstream.** Match to existing workstream by content domain. If no match, propose a new workstream name.
4. **Infer mode.** Apply mode classification. Mode is the work type, not the current state:
   - External consequence or risk language -> `threat`
   - Excitement, strategic upside, identity-alignment -> `hunt`
   - System creation, architecture, infrastructure -> `build`
   - Appears to be a recurring shape -> `farm`
   - Low-energy, maintenance, bureaucratic -> `admin`
   - Small, fast, clears mental load -> `quick-win`
   - When in doubt -> `admin` (conservative default)
5. **Infer status.** Apply status classification independently from mode: [CHANGED v2.1]
   - Explicitly waiting on someone/something -> `status: waiting` with `depends_on` filled
   - Cannot proceed, named blocker -> `status: blocked` with `blocker` filled
   - Otherwise -> `status: open`
6. **Infer effort.** If the input gives clear scope signals, set `effort`. Otherwise leave null. Do not guess. [NEW v2.1]
7. **Infer priority signals.** Extract deadline, urgency language, consequence severity.
8. **Check for duplicates.** Semantic similarity against existing tasks. Flag rather than silently skip.
9. **Present for confirmation.** Show extracted tasks with proposed workstream, mode, status, effort, and due_date. The operator confirms, adjusts, or rejects before write.

**What does NOT qualify as a task:**
- Information shared with no action required
- Completed actions with no follow-up
- Vague aspirations with no concrete next step
- Tasks clearly owned by someone else with no involvement from the operator

### Step 3: Update Tasks

Match by `id` (preferred) or natural language. Show candidates on ambiguous match.

Update fields. Update `last_touched`. Set `completed_date` on done. Require `dropped_reason` on dropped. Require `blocker` on blocked. Require `depends_on` on waiting. [CHANGED v2.1]

**When changing status to blocked or waiting, do not change mode.** The mode should still reflect what kind of work this is when it is unblocked. [CHANGED v2.1]

**On any task change within a workstream, update that workstream's `reentry_context`.** This is not optional. All four subfields (last_action, current_state, next_move, blocker) must reflect the current state. [CHANGED v2.1]

**Bulk operations:** "Mark all Apollo tasks done," "reprioritize everything due this week," "drop all admin tasks older than 30 days." Confirm before writing when 5+ tasks affected.

### Step 4: Triage

Triage is the intelligence layer. It answers: "what is the minimum move that changes the board?"

**Triage protocol:**

1. **Threats first.** All `mode: threat` tasks, regardless of status. What is dangerous right now?
2. **Overdue items.** `due_date` < today, not done/dropped.
3. **Stale items.** `status: open`, `last_touched` > 14 days.
4. **Stale workstreams.** Workstreams with `last_activity` > 14 days that are still `active`. These represent context decay.
5. **Blocked items.** All `status: blocked`. Evaluate: has the blocker changed? Is the block still real? Can it be unblocked with a quick action? [CHANGED v2.1: now purely status-driven]
6. **Waiting items.** All `status: waiting`. Who are we waiting on? How long? Is a nudge or escalation warranted? [CHANGED v2.1: now purely status-driven]
7. **Leverage scan.** Which open tasks have `leverage` filled? Which unblock the most downstream work? Surface the highest-leverage move.
8. **Priority inflation check.** If >30% of active tasks are `mode: threat` or `mode: hunt`, flag inflation. Force-rank: what actually matters this week?
9. **Capacity check.** Two methods, used together: [CHANGED v2.1: effort-aware]
   - **Count-based:** If >15 active items, flag capacity pressure. If >25, flag overload.
   - **Effort-based (when effort data exists):** Sum active effort using S=0.5, M=1.5, L=5, XL=12 hours. If total > 40h (one work week), flag pressure. If > 80h, flag overload. Report both the count and the effort sum.
   - If <50% of active tasks have `effort` set, note that capacity estimate is partial.
10. **Subtask rollup.** For any task with children (other tasks pointing to it via `parent_id`), show completion status: "Task #12: 3/5 subtasks done." Flag XL tasks with no subtasks. [NEW v2.1]
11. **Farm detection.** Scan active tasks and (if loaded) archive for recurrence patterns. Look for: same verb+object shape, same workstream, similar context. Any pattern appearing 3+ times gets flagged: "This looks like a pattern. Should this become an automation or template?" Note: farm detection across sessions requires the archive file to be loaded. If the archive is not loaded, detection is limited to the active file only. [CHANGED v2.1: clarified scope]
12. **Quick-win sweep.** Surface `mode: quick-win` items as easy momentum clearing.
13. **Orphan check.** Surface subtasks whose parent has been marked `done` or `dropped` but the subtask is still open. [NEW v2.1]

**Triage output format:**

```
## BOARD STATE
Active: {n} | Overdue: {n} | Blocked: {n} | Waiting: {n} | Stale: {n}
Effort loaded: {n}/{total active} tasks | Estimated active effort: {n}h

## THREATS
{list or "None active"}

## LEVERAGE MOVES
{highest-leverage open tasks - what unblocks the most}

## OVERDUE
{list with recommended action per item}

## BLOCKED / WAITING
{list with blocker/dependency status, days elapsed, and recommended next move}

## STALE WORKSTREAMS
{workstreams with no activity >14 days, with reentry_context summary}

## SUBTASK ROLLUPS
{parent tasks with completion status of children}

## FARM CANDIDATES
{recurring patterns detected, with occurrence count and automation suggestion}

## QUICK WINS
{items clearable in <15 min}

## ORPHANED SUBTASKS
{subtasks whose parent is done/dropped}

## MINIMUM VIABLE MOVE
{the single action that changes the board the most right now}
```

Triage is advisory. Present. The operator decides.

### Step 5: Review Protocol

Two modes, matching the operator's actual review behavior:

**Triggered review (replaces "daily review"):**

The operator does not do lightweight daily hygiene. Reviews happen when triggered by pressure, confusion, inflection, or direct request ("what's on my plate").

- Show: board state summary, threats, overdue, blocked, waiting, new captures since last review
- Surface stale workstreams with reentry_context
- End with minimum viable move
- Update `meta.last_reviewed`

**Deep review (replaces "weekly review"):**

Run full triage (Step 4). Additionally:
- Walk each active workstream. Show reentry_context (all four subfields). Ask: still active, pause, or close?
- Surface all stale items for keep/drop/reclassify
- **Archive pass:** move completed tasks older than 30 days to the archive file. See Archive Mechanics. [CHANGED v2.1]
- Farm detection pass (load archive if available for cross-session pattern detection)
- Orphan check pass
- Effort audit: flag active tasks missing `effort` if >50% lack it
- End with: board state, minimum viable move, next review trigger
- Update `meta.last_reviewed`

**Do not nag about review cadence.** The operator will review when they need to. The system must be ready when they arrive, not guilt-tripping when they don't.

### Step 6: Write Task File

After any modification:
- Update `meta.last_updated`
- Recalculate `meta.active_count` (open + in_progress + blocked + waiting) and `meta.total_count`
- Update affected workstream `reentry_context` (all four subfields) and `last_activity`
- Update affected workstream `task_count`
- Write atomically (temp file, then rename)
- Confirm to user

### Step 7: Emit Constraint Material (Optional)

When the pipeline is active:

```yaml
task_constraint_summary:
  source: task-tracker
  version: "2.2"
  timestamp: {ISO 8601}
  active_tasks: {int}
  estimated_active_effort_hours: {float | null}  # null if <50% of tasks have effort set
  threat_tasks:
    - task_id: {int}
      task: {string}
      workstream: {string}
      due_date: {date | null}
      effort: {S | M | L | XL | null}
  overdue_tasks:
    - task_id: {int}
      task: {string}
      due_date: {date}
      days_overdue: {int}
  blocked_tasks:
    - task_id: {int}
      task: {string}
      blocker: {string}
      mode: {string}  # preserves work type even when blocked
  waiting_tasks:
    - task_id: {int}
      task: {string}
      depends_on: {string}
      days_waiting: {int}
      mode: {string}  # preserves work type even when waiting
  stale_workstreams:
    - name: {string}
      days_since_activity: {int}
      reentry_context:
        last_action: {string}
        current_state: {string}
        next_move: {string}
        blocker: {string | null}
  upcoming_deadlines:
    - task_id: {int}
      task: {string}
      due_date: {date}
      days_until_due: {int}
  capacity_pressure: none | moderate | high | critical
  capacity_basis: count_only | effort_partial | effort_full
  leverage_moves:
    - task_id: {int}
      task: {string}
      leverage: {string}
```

## Archive Mechanics

[NEW v2.1: entire section]

### When to Archive

Archiving happens only during deep review (Step 5). Not on every write. Not automatically.

Criteria: tasks with `status: done` or `status: dropped` where `completed_date` or `dropped_date` (inferred from `last_touched` for dropped) is > 30 days ago.

### Archive File

Location: same directory as the task file. Default: `~/Documents/tasks/tasks-archive.yaml`. [CHANGED v2.2: updated from Desktop, removed config file reference.]

### Archive Schema

Same task schema as the active file, plus one field:

```yaml
archived_tasks:
  - {all fields from active task schema}
    archived_date: {ISO 8601 date}
```

The archive has no `workstreams` section or `meta` section. It is a flat list of archived tasks.

### Archive Process

1. Identify tasks meeting archive criteria during deep review.
2. Present list to operator: "{n} tasks eligible for archive. Proceed?"
3. On confirmation: append to archive file, remove from active file, recalculate counts.
4. If archive file does not exist, create it.
5. Archive file is append-only. Tasks are never deleted from the archive.

### Archive Loading

The archive is not loaded by default. It is loaded only when:
- Deep review runs farm detection and wants cross-session pattern scanning.
- The operator explicitly asks to search archived tasks.
- The operator asks "have I done this before?" or similar history queries.

Loading the archive is a read-only operation. Archived tasks are never moved back to the active file. If an archived task needs to be re-done, create a new task with fresh context and a note referencing the original.

## Output Contract

### User-Facing Output

After any operation:
- What changed (tasks added, updated, moved, archived)
- Board state summary (active, overdue, blocked, waiting, stale counts, effort estimate if available)
- Minimum viable move if context supports it

Format: concise, tables or bullets, operator-mode. No fluff, no encouragement, no corporate theater.

### Pipeline-Facing Output

The `task_constraint_summary` when the pipeline is active. Machine-readable. Not user-facing.

## Failure Modes

### 1. Capture creep
Adding everything as a task. Fix: qualifying criteria in Step 2. Not every observation, FYI, or completed action is a task.

### 2. Mode inflation
Everything becomes threat or hunt. Fix: triage protocol checks. Conservative default (admin). The 30% ceiling on threat+hunt.

### 3. Reentry context staleness
The reentry_context subfields get out of sync with actual task state. Fix: mandatory update on every task change within the workstream. All four subfields must be refreshed. This is the single most important maintenance operation. [CHANGED v2.1: references structured subfields]

### 4. Workstream proliferation
Too many workstreams, each with 1-2 tasks. Fix: merge small related workstreams. Target: 4-8 active workstreams. If consistently above 10, the operator is either over-segmenting or genuinely overloaded.

### 5. Phantom completion
Marking done what was actually abandoned. Fix: `done` means performed. `dropped` means abandoned with reason. The distinction is the signal.

### 6. Over-decomposition
Breaking simple tasks into unnecessary subtasks. Fix: default to single tasks. Decompose only when genuinely compound. `parent_id` linkage is optional, not mandatory. Most tasks should have `parent_id: null`. [CHANGED v2.1: references parent_id]

### 7. Context loss
Tasks without provenance. Fix: `context` field required. Always answerable: "where did this come from?"

### 8. File drift
File diverges from reality during quiet periods. Fix: stale workstream detection. The 14-day flag is the canary.

### 9. Admin burial
Admin tasks crowd out hunt/build work in the display. Fix: triage separates modes. Admin is batched at the bottom. Hunt and build get visibility priority after threats.

### 10. Dependency amnesia
Forgetting who we are waiting on or what the external blocker is. Fix: `depends_on` required when `status: waiting`. `blocker` required when `status: blocked`. Waiting and blocked items surface in every triage with the person/condition and elapsed time. [CHANGED v2.1: enforced via status requirements]

### 11. Mode/status conflation
[NEW v2.1] Changing mode when a task gets stuck instead of changing status. Fix: mode describes work type, status describes current state. When a task gets blocked, change `status` to `blocked` and leave `mode` alone. If the LLM sets mode to reflect current state rather than work type, triage flags the inconsistency.

### 12. Effort drift
[NEW v2.1] Effort estimates that are never set, making capacity reasoning impossible. Fix: during deep review, flag when >50% of active tasks lack effort. Do not require effort on capture (friction kills adoption), but surface the gap during review.

### 13. Orphaned subtasks
[NEW v2.1] Parent task marked done/dropped while subtasks remain open. Fix: triage orphan check. Surface orphans for the operator to resolve (complete, re-parent, or drop).

### 14. Destructive write
[NEW v2.1] Bad data written to the task file with no recovery path. This is a known gap. The atomic write (temp file then rename) prevents corruption but not bad content. Mitigation: if the task file is stored in a git-tracked directory or iCloud, version history provides recovery. Recommend: keep `tasks.yaml` in a git-initialized directory and commit after deep reviews. The skill does not manage git operations itself.

## Calibration Notes

### Behavioral Model This Skill Is Built For

This skill is calibrated for an operator who:
- Thinks in workstreams and parallel fronts, not atomic checklists
- Hands over messy, compound, high-context material and expects structured decomposition
- Prioritizes by leverage and threat, not by generic urgency labels
- Does not do lightweight daily review hygiene, reviews episodically and deeply when triggered
- Has many parallel threads and needs cheap re-entry, not full context reconstruction
- Values automation of recurring patterns over permanent manual tracking
- Has uneven, spiky workloads across multiple domains (work, IP, legal, personal)
- Uses conversation as temporary working memory and offloads recall to AI tools
- Applies the heuristic: "If it annoys me I automate it, if it excites me I hunt it, if it scales without me I farm it"
- Uses the decision loop: constraint scan, threat model, minimum viable move

If the operator's behavior changes materially, recalibrate the mode definitions, triage weights, and review protocol.

### Integration with Planned Skills

- **unfinished-threads-auditor (L3, planned):** Could feed task-tracker directly. Unfinished threads become task candidates.
- **leverage-vs-load-evaluator (L3, planned):** Could consume the task file for effort/impact scoring. The leverage scan in triage is a lightweight precursor. The `effort` field provides the load input this skill will need. [CHANGED v2.1: effort field enables this integration]

### Task Volume

Expected steady-state: 15-40 active tasks across 4-8 workstreams. If consistently above 50 active tasks, the operator is under-triaging or the scope has expanded beyond personal task tracking.

With effort data: expected steady-state active effort of 20-60 hours. If consistently above 80 hours, the operator is overcommitted.

### File Portability

Plain YAML. Readable by any text editor, parseable by any language, syncable via iCloud/Git, consumable by Shortcuts/Raycast/scripts, manually editable.

**Version history recommendation:** Store `tasks.yaml` in a git-initialized directory. Commit after deep reviews. This provides undo capability that the skill itself does not implement. [NEW v2.1]
