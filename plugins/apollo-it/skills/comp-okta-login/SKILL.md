---
name: comp-okta-login
description: >-
  Self-service troubleshooting for Apollo employees with Okta or SSO login issues.
  Use whenever someone can't log in, is locked out, has MFA or Okta Verify problems,
  forgot their password, their Mac or Windows password isn't working, or needs
  new hire account setup help.
---

# Okta Login Issues — Employee Self-Service

Hey! 👋 Let's get you back in. Tell me what's happening and I'll walk you through it.

______________________________________________________________________

## What's your situation?

Ask the user to describe their issue, then load `references/scenarios.md` for the full troubleshooting steps for each scenario:

- **Scenario A** — MFA / Okta Verify not working (push not arriving, iOS Slack, lost phone)
- **Scenario B** — Forgot password / can't log in
- **Scenario C** — MacBook locked / "Your account is locked"
- **Scenario C-alt** — Windows laptop locked
- **Scenario D** — Okta account locked (too many failed attempts)
- **Scenario E** — New hire / first-time setup not working

If none of the self-serve steps resolve the issue, before invoking `it-human-escalation` tell the user which scenario was attempted and why it didn't work. For example:

> I walked you through [Scenario X — description], but the steps didn't resolve the issue. Let me open a ticket with IT so a human agent can take over.

Then invoke the `it-human-escalation` skill with the full context of what was tried.
