---
name: token-efficiency-assessment
description: Run an interactive token efficiency self-assessment for Claude Code users. Activate when the user wants to check their token habits, assess token efficiency, prepare for a budget increase request, or says 'token efficiency assessment', 'token quiz', or 'check my token usage habits'.
allowed-tools: Bash Write Read
---

# Token Efficiency Assessment

Walk the user through a hybrid self-assessment: a Python script auto-detects 7 configuration signals from the filesystem, and Claude asks ~15 judgment-based questions. Results are stored in Notion (or locally if the MCP is unavailable).

Engineers requesting more token budget run this first — EMs review the results.

Read `references/references.md` in this skill's directory for the Notion database ID, data source ID, efficiency guide URL, and Notion MCP install instructions.

## Instructions

### Step 1 — Detect user name

Check `git config user.name`, then Notion MCP `get-users` with `user_id: "self"`, then `whoami`. Do NOT ask. Use the system username as a last resort.

### Step 2 — Run the env scan

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

### Step 3 — Ask judgment questions (4 rounds)

Present questions one round at a time using `AskUserQuestion`. After each round, briefly note any red flags or strong practices you observe.

**Round 1 — Usage root cause + context hygiene**

Ask these 4 questions:

- Why do you think your usage is high? (multi-select, max 4 options)
  Options: Long conversations, Large context/logs pasted, Heavy Opus usage, Not sure
- Are you using `/compact` or `/clear` to manage context?
  Options (key → value): "Proactively, before it gets full" → `yes`; "Sometimes, when reminded" → `sometimes`; "Rarely or never" → `no`
- Last time you ran `/context` — what % was your context window at?
  Options: "Under 50%" → `under_50`; "50–80%" → `50_to_80`; "Over 80%" → `over_80`; "Haven't checked recently" → `unsure`
- Do you check your token usage in the ccflare dashboard?
  Options: "Yes, regularly" → `yes`; "No / don't know how" → `no`; "I don't have access" → `unsure`

**Round 2 — Context loading habits**

Ask these 4 questions:

- Are you starting fresh conversations for new tasks, or letting context grow?
  Options: "Fresh per task" → `yes`; "Sometimes reset, sometimes continue" → `sometimes`; "Rarely start fresh" → `no`
- When sharing logs or stacktraces, do you paste inline or point Claude to files?
  Options: "Point to files on disk" → `files`; "Mix of both" → `mix`; "Paste inline" → `inline`
- Do you paste images into chat?
  Options: "Never / rarely" → `never`; "Sometimes" → `sometimes`; "Often" → `often`
- Are you writing prompts and comments in English?
  Options: "Yes, always" → `english`; "Mix of English and another language" → `mixed`; "Primarily non-English" → `non_english`

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

### Step 4 — Collect answers and score

After all 4 rounds, construct the answers JSON using the `→ value` mappings above. Use the root_cause multi-select labels as-is. For any question the user skipped, use `""` as the value (scores 0).

Write answers to `/tmp/tea-answers.json`:

```json
{
  "root_cause": ["Long conversations"],
  "uses_compact": "yes",
  "context_window_pct": "under_50",
  "checks_ccflare": "yes",
  "fresh_conversations": "yes",
  "log_sharing": "files",
  "image_pasting": "never",
  "prompt_language": "english",
  "model_switching": "yes",
  "opus_only": "yes",
  "opusplan_known": "yes_use",
  "prompt_quality": "specific",
  "uses_plan_mode": "yes",
  "batching": "yes",
  "subagent_overuse": "no",
  "mcp_payloads_reasonable": "yes"
}
```

Run score.py:

```bash
SKILL_DIR="$(find ~/.claude/plugins "$PWD" -maxdepth 8 -path '*/token-efficiency-assessment/scripts/score.py' -exec dirname {} \; 2>/dev/null | head -1)"
python3 "$SKILL_DIR/score.py" --env /tmp/tea-env.json --answers /tmp/tea-answers.json
```

### Step 5 — Generate top-3 recommendations

Read the `red_flags` list from the score output. Each env-signal red flag includes a `fix` field (specific, actionable). Use these plus context from the user's answers to write the **top 3 improvement recommendations**, ordered by impact. Link to the efficiency guide from `references/references.md`.

### Step 6 — Present results

Show:

- Numeric score: "Score: **N/22**"
- Verdict: "Budget readiness: **Yes** / **Needs improvement** / **No**"
  - 18–22: Ready for budget increase — strong habits
  - 12–17: Needs improvement — address gaps before requesting more budget
  - 0–11: Not ready — significant changes needed
- Areas of strength (list from `strengths`)
- Top 3 improvement recommendations with links

### Step 7 — Store results

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
| Red Flags | Bulleted list of red flags (label only, omit fix text) |
| Recommendations | Top 3 recommendations |
| Budget Ready | "Yes" / "Needs improvement" / "No" |

Share the Notion URL with the user and remind them to share it with their EM if requesting a budget increase.

#### If the Notion MCP is NOT available

Save results as JSON to `~/.claude/token-efficiency-assessments/<name>-<date>.json` using the same field structure as the existing assessments in that directory (compatible with the format in `references/references.md`).

Tell the user where the file was saved, then print the Notion MCP install instructions inline:

- Install: `claude mcp add notion -- npx -y @anthropic-ai/notion-mcp-server`
- Set `NOTION_TOKEN` in `~/.claude/settings.json` env section
- Share the Notion DB with the integration
- Re-run the skill to push saved results to Notion
