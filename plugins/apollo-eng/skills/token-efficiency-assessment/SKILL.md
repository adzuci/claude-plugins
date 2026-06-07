---
name: token-efficiency-assessment
description: Run an interactive token efficiency self-assessment for Claude Code users. Activate when the user wants to check their token habits, assess token efficiency, prepare for a budget increase request, or says 'token efficiency assessment', 'token quiz', or 'check my token usage habits'.
allowed-tools: Bash Write Read
---

# Token Efficiency Assessment

Walk the user through a hybrid self-assessment: Python scripts auto-detect 8 configuration signals from the filesystem and context window, and Claude asks ~15 judgment-based questions. Results are stored in Notion (or locally if the MCP is unavailable).

Run this to get a personalized snapshot of your Claude Code habits and a prioritized improvement plan. EMs also use results to guide budget decisions.

Read `references/references.md` in this skill's directory for the Notion database ID, data source ID, efficiency guide URL, and Notion MCP install instructions.

## Instructions

### Step 0 — Set expectations upfront

Before doing anything else, tell the user:

> "This assessment takes about 5 minutes. I'll auto-detect some signals from your environment, then ask ~15 questions about your habits.
>
> **Your results will be saved to a shared Notion database** that EMs use to understand how the team is using Claude Code and where we can all improve together — the goal is collective growth, not gotcha. If the Notion MCP isn't set up, I'll save locally instead and walk you through how to connect it."

Then proceed.

### Step 1 — Detect user name

Check `git config user.name`, then Notion MCP `get-users` with `user_id: "self"`, then `whoami`. Do NOT ask. Use the system username as a last resort.

### Step 2 — Run context analysis

Run `/context` first (before any file reads or tool calls that would pollute the baseline). Capture the output to `/tmp/tea-context-raw.txt`, then analyze it:

```bash
SKILL_DIR="$(find ~/.claude/plugins "$PWD" -maxdepth 8 -path '*/token-efficiency-assessment/scripts/analyze_context.py' -exec dirname {} \; 2>/dev/null | head -1)"
python3 "$SKILL_DIR/analyze_context.py" --input /tmp/tea-context-raw.txt --out /tmp/tea-context.json
```

Read `/tmp/tea-context.json`. If there are issues (items that shouldn't be in context), show them to the user:

```
Context analysis:
  Baseline: 12% (threshold: 15%) ✓
  Issues found:
    ✗ node_modules/lodash/index.js (15%) — node_modules should be in .claudeignore
    ✗ package-lock.json (8%) — package-lock.json is large; consider .claudeignore

  Suggested fix — add to .claudeignore:
    node_modules/
    package-lock.json
```

If baseline is OK and no issues, show a brief success message. Do not ask about context — this is auto-detected.

### Step 3 — Run the env scan

Run the deterministic environment scan (stdlib Python, no external deps):

```bash
SKILL_DIR="$(find ~/.claude/plugins "$PWD" -maxdepth 8 -path '*/token-efficiency-assessment/scripts/check_env.py' -exec dirname {} \; 2>/dev/null | head -1)"
python3 "$SKILL_DIR/check_env.py" --out /tmp/tea-env.json
```

Read `/tmp/tea-env.json`. Show the user a brief summary — one line per signal:

- Green check (✓) for score=1 signals
- Red flag (✗) for score=0 signals, with the `fix` text

Example:

```
Auto-detected signals:
  ✓ .claudeignore configured
  ✓ CLAUDE.md is lean (45 lines)
  ✗ Tool Search threshold not tuned — set toolSearchThreshold: 0.05 in settings.json
  ...
```

Do not ask the user about these signals — they are already scored.

### Step 4 — Ask judgment questions (4 rounds)

Before Round 1, tell the user: "I'll ask about your habits across four areas — no wrong answers, just be honest so the recommendations are as useful as possible."

Present questions one round at a time using `AskUserQuestion`. After each round, briefly note any strong practices or opportunities to improve you observe.

**Round 1 — Usage root cause + context hygiene**

Ask these 3 questions:

- Why do you think your usage is high? (multi-select, max 4 options)
  Options: Long conversations, Large context/logs pasted, Heavy Opus usage, Not sure
- Are you using `/compact` or `/clear` to manage context?
  Options (key → value): "Proactively, before it gets full" → `yes`; "Sometimes, when reminded" → `sometimes`; "Rarely or never" → `no`
- Last time you ran `/context` — what % was your context window at?
  Options: "Under 50%" → `under_50`; "50–80%" → `50_to_80`; "Over 80%" → `over_80`; "Haven't checked recently" → `unsure`
- Do you use `/cost` to check your token spend mid-session?
  Options: "Yes, regularly" → `yes`; "Sometimes" → `sometimes`; "No / didn't know about it" → `no`

After Round 1, give inline tips for any low answers:

- `uses_compact: no` → "Tip: `/compact` summarizes your context mid-task without losing thread — try it when context feels heavy or you're switching subtasks."
- `context_window_pct: over_80` → "Tip: Over 80% is a warning sign — run `/compact` now or `/clear` if the task has shifted."
- `checks_cost: sometimes` → "Tip: Making `/cost` a habit before big tasks gives you a quick gut-check on spend before you're deep in."
- `checks_cost: no` → "Tip: `/cost` shows your running token spend for the current session — quick to check before kicking off a big task."

If the user selected "Not sure" for the root cause question, offer to run `/insights` now before continuing to Round 2: "Want me to pull your actual usage data so you can answer the next questions with real numbers? I can run `/insights` for you." If they agree, invoke the insights skill using the Skill tool and show the output, then continue.

**Round 2 — Context loading habits**

Ask these 3 questions:

- Are you starting fresh conversations for new tasks, or letting context grow?
  Options: "Fresh per task" → `yes`; "Sometimes reset, sometimes continue" → `sometimes`; "Rarely start fresh" → `no`
- When sharing logs or stacktraces, do you paste inline or point Claude to files?
  Options: "Point to files on disk" → `files`; "Mix of both" → `mix`; "Paste inline" → `inline`
- Do you paste images into chat?
  Options: "Never / rarely" → `never`; "Sometimes" → `sometimes`; "Often" → `often`

After Round 2, give inline tips for any low answers:

- `fresh_conversations: no` → "Tip: Each task gets cheaper when you start fresh — old context from unrelated work just adds noise."
- `log_sharing: inline` → "Tip: Pasting logs inline bloats context fast. Point Claude to the file path instead — it reads only what it needs."
- `image_pasting: often` → "Tip: Images are expensive per token. Use file paths or text descriptions where possible."

**Round 3 — Model selection and prompt quality**

Ask these 4 questions:

- Are you using `/model` to switch to Haiku or Sonnet for simple tasks (linting, small edits)?
  Options: "Yes, regularly" → `yes`; "Sometimes" → `sometimes`; "No, I stay on Opus" → `no`
- Are you using Opus only when the task genuinely needs deep reasoning?
  Options: "Yes, selectively" → `yes`; "Sometimes" → `sometimes`; "I use Opus for everything" → `no`
- Do you know about `opusplan` mode (`/model opusplan`) — Opus for planning, Sonnet for execution?
  Options: "Yes, and I use it" → `yes_use`; "I know about it but don't use it" → `yes_know`; "I didn't know about it" → `no`
- How would you describe the quality of your prompts?
  Options: "Very specific — one clear task per message" → `specific`; "Mix of specific and vague" → `mixed`; "Often vague, causing back-and-forth" → `vague`

After Round 3, give inline tips for any low answers:

- `model_switching: no` → "Tip: `/model sonnet` for linting, small edits, or Q&A can cut per-task cost by 5–10×."
- `opus_only: no` → "Tip: Opus is best for complex reasoning and architecture. For routine tasks, Sonnet gets the job done cheaper."
- `opusplan_known: no` → "Tip: `/model opusplan` uses Opus to plan, then Sonnet to execute — best of both worlds."
- `prompt_quality: vague` → "Tip: One clear task per message prevents back-and-forth. More specific = fewer turns = fewer tokens."

**Round 4 — Workflow patterns**

Ask these 4 questions:

- Are you using `/plan` before large tasks to align on approach before burning tokens on implementation?
  Options: "Yes, consistently" → `yes`; "Sometimes" → `sometimes`; "Rarely" → `no`
- Are you batching related changes in one conversation rather than many small ones?
  Options: "Batch related work" → `yes`; "Mix" → `sometimes`; "Many small conversations" → `no`
- Are you using the Agent/subagent tool when Grep or Glob would be faster and cheaper?
  Options: "No, I prefer Grep/Glob" → `no`; "Sometimes use subagents unnecessarily" → `sometimes`; "Often reach for subagents first" → `yes`
- Are MCP tool calls returning excessively large payloads (thousands of lines)?
  Options: "No, payloads are reasonable" → `yes`; "Sometimes large" → `sometimes`; "Often very large" → `no`

After Round 4, give inline tips for any low answers:

- `uses_plan_mode: no` → "Tip: `/plan` aligns on approach before burning tokens on implementation — saves retries when the direction is wrong."
- `batching: no` → "Tip: Related changes in one conversation share context — spinning up a new one for each small task restarts the overhead."
- `subagent_overuse: yes` → "Tip: For file searches, `Grep` and `Glob` are 10–100× cheaper than spinning up a subagent."

### Step 5 — Collect answers and score

After all 4 rounds, construct the answers JSON using the `→ value` mappings above. Use the root_cause multi-select labels as-is. For any question the user skipped, use `""` as the value (scores 0).

Write answers to `/tmp/tea-answers.json`:

```json
{
  "root_cause": ["Long conversations"],
  "uses_compact": "yes",
  "context_window_pct": "under_50",
  "fresh_conversations": "yes",
  "log_sharing": "files",
  "image_pasting": "never",
  "model_switching": "yes",
  "opus_only": "yes",
  "opusplan_known": "yes_use",
  "prompt_quality": "specific",
  "uses_plan_mode": "yes",
  "batching": "yes",
  "subagent_overuse": "no",
  "mcp_payloads_reasonable": "yes",
  "checks_cost": "yes"
}
```

Run score.py with both env and context signals:

```bash
SKILL_DIR="$(find ~/.claude/plugins "$PWD" -maxdepth 8 -path '*/token-efficiency-assessment/scripts/score.py' -exec dirname {} \; 2>/dev/null | head -1)"
python3 "$SKILL_DIR/score.py" --env /tmp/tea-env.json --context /tmp/tea-context.json --answers /tmp/tea-answers.json
```

### Step 6 — Generate top-3 recommendations

Read the `red_flags` list from the score output (these are the "Growth Areas" shown to the user). Each env-signal and context-signal item includes a `fix` field (specific, actionable). Use these plus context from the user's answers to write the **top 3 improvement recommendations**, ordered by impact. Link to the efficiency guide from `references/references.md`.

### Step 7 — Present results

Show in this order:

1. Numeric score: "Score: **N/M**" where M is `score_max` from the score output (22 without context signal, 23 with)
1. Verdict: "Efficiency level: **Ready** / **Almost There** / **Building Habits**"
   - Ready — strong habits across the board
   - Almost There — a few targeted improvements will make a big difference
   - Building Habits — real room to grow, and the recommendations below are concrete and quick to act on
1. **What's working well** — open with "Here's what's working well for you:" followed by the `strengths` list (capped at 5)
1. **Partial-credit callout** — count `answer_scored` keys with score 0.5. If there are 3 or more, add: "You have N habits you're doing 'sometimes' — these are your quickest wins. Moving any one of them to consistently would bump your score meaningfully."
1. **Biggest opportunities** — open with "Here's where the biggest gains are:" followed by the top 3 recommendations with links

When the verdict is "Building Habits", acknowledge the score honestly then end on a constructive note — e.g., "The good news: the top recommendations below are concrete and quick to act on."

After showing results, offer to run `/insights` for the user to pull their actual token usage data from ccflare. Say: "Want me to pull your actual usage breakdown? I can run `/insights` now to see where your tokens are really going." If they agree, invoke the insights skill using the Skill tool.

### Step 8 — Store results

#### If the Notion MCP is available

Check if `notion-create-pages` or similar Notion MCP tools are available. If so, create a page in the Notion database using the database ID from `references/references.md`.

Properties to set:

| Property | Value |
|---|---|
| Name | User's name |
| date:Date:start | Today's date (ISO 8601) |
| Score | Numeric score (e.g., 17) |
| Usage Habits | Section 1 answers, summarized |
| Workflow & Config | Section 2 answers, summarized |
| Strengths | Bulleted list of strengths |
| Growth Areas | Bulleted list of growth areas (label only, omit fix text) |
| Recommendations | Top 3 recommendations |
| Efficiency Level | "Ready" / "Almost There" / "Building Habits" |

Share the Notion URL with the user and remind them to share it with their EM if requesting a budget increase.

> **Note for admins:** The Notion database still has columns named "Budget Ready" and "Red Flags" — rename them to "Efficiency Level" and "Growth Areas" in the Notion UI (the MCP API rejected the schema change). Until that rename is done, write to "Budget Ready" and "Red Flags" instead of the names in the table above.

#### If the Notion MCP is NOT available

Save results as JSON to `~/.claude/token-efficiency-assessments/<name>-<date>.json` using the same field structure as the existing assessments in that directory (compatible with the format in `references/references.md`).

Tell the user where the file was saved, then print the Notion MCP install instructions inline:

- Install: `claude mcp add notion -- npx -y @anthropic-ai/notion-mcp-server`
- Set `NOTION_TOKEN` in `~/.claude/settings.json` env section
- Share the Notion DB with the integration
- Re-run the skill to push saved results to Notion
