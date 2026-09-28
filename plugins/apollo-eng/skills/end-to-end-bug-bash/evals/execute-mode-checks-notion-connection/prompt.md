---
name: execute-mode-checks-notion-connection
tags: [routing, execution-phase, notion, bug-bash]
max_turns: 3
allowed_tools: []
append_system_prompt: |-
  You must follow the instructions below exactly, as if invoked via
  `/apollo-eng:end-to-end-bug-bash`. There is no Notion MCP tool available to you in this
  session at all — none exists in your tool list, and none will appear if you look for one.
  Do not use any tools. Respond only in chat.

  # end-to-end-bug-bash (excerpt injected as if via direct slash-command invocation)

  ## Select the operating mode

  | User intent | Mode | Run |
  | --- | --- | --- |
  | Execute, verify, retest, or mark existing cases pass/fail | **Execute** | Phase 0 (execution inputs: environment URL, credentials, VPN check; plus §0.4 Notion MCP/evidence-upload check when the source is Notion), then fetch the existing cases, then Phases 3-4; add Phase 5 only for a campaign |

  ## Phase 0 — Intake

  ### 0.4 MCP connection check (before asking anything else)

  A missing tool connection discovered mid-run — failing to fetch a Notion board after gathering
  research context, or failing to create the Notion test plan after execution — wastes real work and
  breaks the seamless, uninterrupted run this skill is meant to provide. Check this now, before
  proceeding:

  - **Notion MCP — check when Notion is a source or destination.** This is required for Full mode,
    Notion delivery in Generate mode, and Notion-sourced Execute mode. A local generation or
    user-provided execution does not require Notion.
  - **Notion evidence upload — check before any Notion-sourced execution.**

  Use `ToolSearch` (or equivalent tool-discovery mechanism) to confirm the relevant MCP tools are
  actually present in this session's toolset. If something needed is missing, tell the user plainly
  which connection is missing and why, and ask them to connect it before continuing — don't assume the
  skill can auto-connect it. Once confirmed connected (or the user says that source isn't needed after
  all), proceed.

  ### 0.5 / 0.6 — environment URL and credentials

  Reuse a saved authenticated session or login/password already supplied in the conversation; do not
  re-ask for values already given.
---

Teammate's message:

"Execute the test plan at this Notion page: https://www.notion.so/apolloio/Sample-Feature-Test-Plan-abc123.
Use staging, base URL https://staging.example.com, login qa@apollo.io, password Testpass123!.
Go ahead and run it."

Environment URL and credentials are already supplied above — do not ask for those again.
Respond to the teammate now, following the injected instructions exactly.
