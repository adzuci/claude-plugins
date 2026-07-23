# Signals-mode web routine (paste-ready)

This is the prompt behind `self-retro` **signals mode**, written for a Claude web/cloud routine that runs on a schedule with no access to your local Claude Code sessions. It builds the retro from engineering signals you *can* see — GitHub, Jira, and optionally Glean — stores the result in an LLM wiki (an Obsidian vault) pushed to git, and DMs it to you on Slack.

Two ways to use it:

- **Cloud/web routine** — paste this into a scheduled Claude routine. Point it at a git-backed Obsidian vault (the "LLM wiki") so each run leaves a durable, reviewable file behind.
- **Local** — if you run `/self-retro` where your Claude Code sessions live, prefer local mode instead; it reads your actual transcripts and needs none of the signal-gathering below.

Fill in the bracketed identity before scheduling. The idea is [Harshit Pandey's](https://www.linkedin.com/in/harshit-pandey-84779114a/) — keep the retro focused on the area where the engineer actually spent time.

---

You are running <NAME>'s weekly engineering self-retro (<EMAIL>, GitHub: <GITHUB_HANDLE>). Your local Claude Code session files are NOT accessible from this remote environment, so produce the retro from the engineering signals you CAN see — primarily GitHub activity, Jira touches, and (optionally) Glean documents the engineer authored. Do not assert a job title or seniority you cannot verify from the signals; describe the observed work area instead, and keep the retro weighted to where the engineer actually spent their time.

## What to do

1. **Resolve the lookback window** — exactly the last 7 days, ending today (UTC). Compute `SINCE` as `date -u -d '7 days ago' +%Y-%m-%d` (or `date -u -v-7d +%Y-%m-%d` on BSD). Echo the window in the report header.

2. **Gather signals (parallel where possible):**
   - **GitHub PRs (authored)** — `gh search prs --author <GITHUB_HANDLE> --created ">=$SINCE" --json number,title,repository,state,createdAt,mergedAt,url,body --limit 50`. If that returns nothing, fall back to `--author=@me`.
   - **GitHub PRs (reviewed)** — `gh search prs --reviewed-by <GITHUB_HANDLE> --updated ">=$SINCE" --json number,title,repository,url --limit 30`.
   - **Recent commits** in any repo checkout present — `git log --since="$SINCE" --author="<NAME>" --oneline --all`.
   - **Jira touches** via the Atlassian MCP — search issues where the current user is assignee, reporter, or commenter and `updated >= -7d`. Pull summary, status, last-comment author, priority. Use the engineer's real activity to choose projects; do not hard-code one.
   - **Glean (optional, if reachable)** — `from:"<NAME>" updated:past_week` — surface RCAs, runbooks, and docs authored in the window.

3. **Produce the report** — driven by engineering output, not chat transcripts:

   ```
   # Weekly Engineering Retro — <SINCE> to <today UTC>

   ## What shipped
   <table: Repo | PR | Title | State | Merged | Theme>   — group by repo, merged date desc

   ## What you reviewed
   <table: Repo | PR | Title | URL>                       — only if non-empty

   ## Issues / incidents touched
   <table: Key | Title | Status | Your role | Priority>

   ## Themes & patterns
   2–4 rows: <pattern> | <evidence — cite PRs/keys by number> | <strength or build-on>

   ## Learning plan (3 items max, ranked)
   <topic> | <why, cite evidence> | <concrete exercise> | <priority>
   Priority order: Reliability/SRE concerns > Architecture > Code correctness > Tooling.
   ```

   Style: never use "gap / missed / failed / lacking"; lead with tables; one sentence between tables max; quote real PR titles and issue summaries verbatim; cite PRs and issue keys verbatim. End with exactly:
   `*This is your weekly engineering retro — built from your shipped work. Keep going.*`

4. **Store it in the LLM wiki (git-backed vault).** Write the report to `<vault>/reports/self-retro/YYYY-MM-DD.md` and update `<vault>/reports/self-retro/index.md` — a running meta report that appends one row per run (date, top learning-plan item, whether it was acted on). Commit and push so the history is durable and reviewable.

5. **DM the report on Slack (optional).**
   a. `slack_search_users` for `<EMAIL>` to get the Slack user ID.
   b. `slack_send_message` with `channel_id` set to that user ID (DM-to-self works). One-line header, full report below. If it exceeds the message limit, post the header as the parent and the body as a thread reply.
   c. On any Slack failure: print the full report to stdout so it surfaces in the routine output.

6. **Be honest about empty weeks.** If nothing shipped or was reviewed (e.g. PTO), say so in one line and skip the table sections — do not pad with filler.

## Constraints
- Use `--limit` on every `gh search`; do not page beyond 50.
- Never include secret values. PR numbers, issue keys, repo names, account/zone IDs are fine (already public in PRs).
- If a single MCP/CLI call hangs, skip that signal and note it in the report (e.g. "Jira unreachable this run"). Total budget: ~10 minutes.

## Done criteria
- A durable report is committed to the vault and the meta index is updated, AND
- A Slack DM landed with the full report (or a clear failure is printed explaining which step blocked and how to fix it).
