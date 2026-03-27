---
name: token-efficiency-assessment
description: Run an interactive token efficiency self-assessment for Claude Code users. Activate when the user wants to check their token habits, assess token efficiency, prepare for a budget increase request, or says 'token efficiency assessment', 'token quiz', or 'check my token usage habits'.
---

# Token Efficiency Assessment

Walk the user through a 2-section self-assessment of their Claude Code token usage habits. Engineers requesting more token budget run this first — EMs review the results.

Read `references/references.md` in this skill's directory for the Notion database ID, data source ID, efficiency guide URL, and Notion MCP install instructions.

## Instructions

1. Read `references/references.md` from this skill's directory for all external links and IDs
1. Detect the user's **full name** automatically — check `git config user.name`, or the Notion MCP `get-users` with `user_id: "self"`, or `whoami`. Do NOT ask the user for their name. If none of these work, use the system username.
1. Present questions **one section at a time** using `AskUserQuestion`
1. After each section, briefly note any red flags or good practices
1. After both sections, **score** the user (see Scoring below) and provide a summary
1. **Store results** (see Output section below)

## Questions by Section

### Section 1: Usage & Context Management

Covers basics, context management, and model selection.

- Why do you think your token usage is so high? (multi-select: long conversations, large context/logs, heavy Opus usage, images in chat, non-English prompts, not sure)
- Are you using `/compact` to compress conversation history?
- Have you run `/context` recently — what % was your context window at?
- Have you checked your usage in the **ccflare dashboard**?
- Are you starting fresh conversations for new tasks, or letting context grow unbounded?
- Are you pasting large logs/stacktraces inline, or pointing Claude to files on disk?
- Are you pasting images into chat? (images are especially token-heavy)
- Are you writing prompts and comments in English? (non-English tokenizes 2-3x worse)
- Are you using `/model` to switch to Haiku/Sonnet for simpler tasks (linting, formatting, small edits)?
- Are you using Opus only for tasks that actually need deep reasoning?
- Do you know about `opusplan` mode (`/model opusplan`) for planning?

Present these as 3-4 `AskUserQuestion` calls to keep each one manageable (3-4 questions per call).

### Section 2: Workflow & Configuration

Covers workflow patterns, configuration, guardrails, and MCP/tools.

- Are you giving clear, specific prompts — or vague ones that cause multiple rounds of back-and-forth?
- Are you using `/plan` before large tasks to align on approach before burning tokens on implementation?
- Are you batching related changes in one conversation vs. spreading across many?
- Are you using subagents/Agent tool excessively when Grep/Glob would suffice?
- What permission mode are you using? (auto-accept burns tokens faster if Claude goes off-track)
- Are you using `.claudeignore` to exclude irrelevant dirs (node_modules, build artifacts, vendor)?
- Do you have `--max-turns` or a token budget configured?
- Is your `CLAUDE.md` lean and scannable, or bloated with stale entries?
- What MCPs do you have enabled? (each one adds token cost to every request)
- Are MCP tool calls returning excessively large payloads?
- Have you tuned your Tool Search threshold? (default 10%, 5% can save tokens)
- Are you calling MCP tools repeatedly for info you could cache in CLAUDE.md or memory?

Present these as 3-4 `AskUserQuestion` calls to keep each one manageable (3-4 questions per call).

## Scoring

Score each answer on a 0-1 scale. The first question in Section 1 ("Why do you think your token usage is so high?") is **informational only** — it helps contextualize answers but is not scored. All other questions map to one scored signal each (22 total).

**Positive signals (1 point each):**

- Uses `/compact` or `/clear` proactively
- Context window under 50%
- Checks ccflare dashboard
- Starts fresh conversations per task
- Points Claude to files on disk (not paste inline)
- Does not paste images
- Prompts in English
- Switches models for simple tasks
- Uses Opus only for deep reasoning
- Knows about opusplan
- Writes clear, specific prompts
- Uses `/plan` before large tasks
- Batches related changes
- Does not overuse subagents
- Uses a non-auto-accept permission mode
- Has `.claudeignore` configured
- Has `--max-turns` or token budget set
- Keeps `CLAUDE.md` lean
- Only necessary MCPs enabled
- MCP payloads are reasonable
- Tool Search threshold tuned
- Caches MCP data in CLAUDE.md or memory

**Score → readiness mapping:**

- **18-22:** Ready for budget increase — strong habits
- **12-17:** Needs improvement — address gaps before requesting more budget
- **0-11:** Not ready — significant changes needed

After scoring, present:

- Numeric score (e.g., "Score: 17/22")
- Areas of strength
- Top 3 improvement recommendations (link to the efficiency guide from references/references.md)
- Budget readiness verdict: "Yes", "Needs improvement", or "No"

## Output: Store Results

### If the Notion MCP is available

Check if `notion-create-pages` or similar Notion MCP tools are available. If they are, create a page in the Notion database using the data source ID from `references/references.md`.

Properties to set:

| Property | Value |
|---|---|
| Name | User's name |
| date:Date:start | Today's date (ISO 8601) |
| Score | Numeric score (e.g., 17) |
| Usage Habits | Section 1 answers, summarized |
| Workflow & Config | Section 2 answers, summarized |
| Strengths | Bulleted list of strengths |
| Red Flags | Bulleted list of red flags |
| Recommendations | Top 3 recommendations |
| Budget Ready | "Yes" / "Needs improvement" / "No" |

After creating the page, share the Notion URL with the user and remind them to share it with their EM if requesting a budget increase.

### If the Notion MCP is NOT available

1. Save results as JSON to `~/.claude/token-efficiency-assessments/<name>-<date>.json` with all the fields above
1. Tell the user where the file was saved
1. Point them to `references/references.md` in this skill's directory for instructions on:
   - Installing the Notion MCP server
   - Pushing saved results to Notion after installation
1. Print the key instructions inline:
   - Install: `claude mcp add notion -- npx -y @anthropic-ai/notion-mcp-server`
   - Set `NOTION_TOKEN` in `~/.claude/settings.json` env
   - Share the DB with the integration in Notion
   - Re-run the skill to push results
