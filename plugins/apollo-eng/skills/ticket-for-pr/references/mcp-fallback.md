# MCP fallback

Use this when the `jira` and/or `gh` CLI is unavailable and a matching MCP server is connected. MCP tool names vary between servers and versions (official Atlassian remote MCP, community Jira servers, GitHub MCP), so **discover the actual tools first** — list what the connected server exposes and match by capability, don't assume the names below exist verbatim.

## Capability mapping per workflow step

| Step | CLI | MCP capability to look for |
|---|---|---|
| 1. Read PR | `gh pr view --json ...` | get/read pull request (title, body, files, author, state, merged) |
| 4. Create ticket | `jira issue create` | create issue (project, type, summary, description, assignee) |
| 5. Retitle PR | `gh pr edit --title` | update pull request |
| 6. Link in PR body | `gh pr edit --body` | update pull request |
| 7. Status | `jira issue move` | list transitions + transition issue |

## Jira-side caveats

- **Issue type**: create with the correct type. Some MCP edit tools can change type post-creation, many can't — treat type as effectively immutable, same as the CLI.
- **Description format**: servers differ — some accept markdown, some expect ADF or wiki markup. Check the create-issue tool's parameter schema/description. Keep formatting conservative (paragraphs, simple lists, code fences), and after creating, fetch the issue once to verify the description rendered sanely rather than assuming.
- **Assignee**: many servers want an `accountId`, not an email. If so, resolve the PR author's Jira email (from `CLAUDE.md`) to an accountId via the server's user-search tool before creating; if there's no user-search tool, create unassigned and tell the user.
- **Transitions**: transition names are workflow-specific and servers often require a transition **ID**. List available transitions for the issue first, then pick the one matching "Done"/"In Progress". If a required transition isn't offered (gated on required fields), set those fields first or report back — same rule as the CLI path.
- **Key/URL capture**: take the issue key from the create tool's result. If the result has no browse URL, construct it from the site base URL (`https://<site>.atlassian.net/browse/<KEY>`), confirming the base from server metadata or `CLAUDE.md` rather than guessing the site name.

## GitHub-side caveats

- **Read-modify-write the body**: fetch the current PR body via the get tool, edit it, then send the full updated body — update tools replace the body wholesale, and sending only the new line would wipe the author's description.
- **Repo resolution**: without `git remote -v` (no local checkout), take owner/repo from the PR URL the user gave, or ask.

## What stays identical regardless of tooling

All workflow *decisions* are tool-agnostic: existing-prefix handling (step 2), pre-PR framing of the description (step 3), assignee = PR author, hyperlinked ticket keys only, status derived from PR state, and asking instead of guessing on missing config. Only the command surface changes.
