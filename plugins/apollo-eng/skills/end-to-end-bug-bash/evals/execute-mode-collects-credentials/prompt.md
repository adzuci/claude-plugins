---
name: execute-mode-collects-credentials
tags: [routing, execution-phase, bug-bash]
max_turns: 3
allowed_tools: []
append_system_prompt: |-
  You must follow the instructions below exactly, as if invoked via
  `/apollo-eng:end-to-end-bug-bash`. Do not use any tools. Respond only in chat.

  # end-to-end-bug-bash (excerpt injected as if via direct slash-command invocation)

  ## Select the operating mode

  Infer the mode from the requested outcome. Do not ask the user to choose a mode when their intent is
  already clear.

  | User intent | Mode | Run |
  | --- | --- | --- |
  | Generate, design, review, or export bug-bash cases | **Generate** | Phases 0-2, then stop |
  | Execute, verify, retest, or mark existing cases pass/fail | **Execute** | Phase 0 (execution inputs: environment URL, credentials, VPN check; plus §0.4 Notion MCP/evidence-upload check when the source is Notion), then fetch the existing cases, then Phases 3-4; add Phase 5 only for a campaign |
  | Run a bug bash end to end, including planning and execution | **Full** | Phases 0-5 |

  If the request is ambiguous, prefer the least-mutating interpretation: draft/generate before
  writing to Notion, and inspect existing cases before creating new ones. Ask one concise question
  only when the choice would materially change external writes or browser execution.

  ## Phase 0 — Intake

  **Ask everything in one consolidated round, not one question at a time.**  For
  Apollo-owned test environments, an explicit request to run/execute/test plus a complete environment
  URL and usable primary credentials is the start authorization; do not ask for another "start"
  confirmation.

  Collect only inputs needed by the selected mode. Generate mode does not need login credentials,
  VPN access, execution authorization, evidence-upload capability, or integration authentication
  unless the requested plan itself depends on empirical discovery in a live environment.

  ### 0.5 Environment tier + URL (Execute and Full modes only)

  Ask **staging or production** before anything else environment-related — don't assume:

  - **Staging:** ask for the exact base URL. Never guess or reuse a URL from a prior run/example.
  - **Production:** confirm the exact production base URL to test against as well.

  ### 0.6 Resolve primary account authentication once per run

  Reuse a saved authenticated session or login/password already supplied in the conversation. If
  authentication is still missing, request login and password together in the consolidated ask, not a
  separate round-trip. Never guess a URL or credential.

  ## Phase 3 — Execute (per feature)

  Follow `manual-test-execution`'s mechanics directly — **do not** re-ask for scenario
  source or re-collect credentials, both are already known from Phase 0/2.
---

A teammate already has a local test plan file with 8 written test cases for a "widget export"
feature.

Teammate's message:

"Execute the widget export test plan against staging. I'm ready to start — go ahead."

No environment URL, login, or password has been supplied anywhere in this conversation.
Respond to the teammate now, following the injected instructions exactly.
