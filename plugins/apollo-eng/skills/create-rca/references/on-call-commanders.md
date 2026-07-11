# On-Call Commanders at Apollo

How call commanders work, for context when reconstructing an incident and when telling the user where to get the Zoom recording. Grounded in Slack (#call-commanders, #incident-response-sev0-sev1) as of July 2026.

## Channels

- **#call-commanders** (`C07UD47DF5E`) — the commanders' own channel: rotation/schedule changes, runbook updates, process discussion.
- **#incident-response-sev0-sev1** (`C0362RC2GR2`) — where incidents actually run: incident threads, Zoom bridge links, commander updates. This is usually where the Slack thread(s) fed into this skill live.

## How the Process Works

- Incidents are declared with the incident bot in #incident-response-sev0-sev1: `/incident [sev-0|sev-1|sev-2|sev-3] "[summary]"`. The bot pages the call commander, creates the incident Slack thread, files the INCIDENT Jira ticket, and links a Zoom bridge in the thread.
- Call commanders join SEV-0 (and typically SEV-1) incidents so engineers can focus on mitigation. Commanders facilitate rather than debug: they give regular updates, pull people out of rabbit holes, bring in the right people, and suggest rollbacks/reverts when appropriate.
- The commander updates the Better Stack status page (status.apollo.io) during an active incident and, for SEV-0s, a link to the incident thread goes to support.
- Commanders work a timezone-based rotation (e.g. IST and NAM rotations). Their working docs are the [Call Commander Runbook](https://app.notion.com/p/apolloio/Call-Commander-Runbook-372ab2b3b49681998361f7a33b4da220) and the [Incident Management Process](https://www.notion.so/apolloio/Incident-Management-Process-f0fc71b20cf54c80adebb083d466826c) in Notion.

## Why It Matters for This Skill

- **Zoom recordings**: the incident Zoom bridge is created by the bot and its recording is reachable via the on-call commander — hence this skill's prompt "you can reach out to the on-call commander for access to the Zoom recording."
- **Timeline anchors**: commander updates in the incident thread (declaration, severity changes, status-page updates, disbanding) are high-quality, timestamped timeline entries — link them as Slack permalinks.
