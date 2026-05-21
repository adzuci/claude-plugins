---
last_reviewed: 2026-05-20
---

# Chili Piper

## Role at Apollo

Chili Piper handles two things: inbound lead routing and meeting scheduling.

- Inbound routing: when a lead submits a form or is qualified, Chili Piper assigns them to the correct AE or CSM based on routing rules (territory, segment, round-robin, etc.)
- Scheduling: reps use their Chili Piper personal meeting room URL to let prospects and customers book time directly

## Personal meeting room URL and Gong recording

Reps must use their Chili Piper personal meeting room URL for Gong to record calls. This is the most common cause of missing recordings.

A standard Zoom link sent via email bypasses Chili Piper entirely. Without Chili Piper in the scheduling path, Gong does not receive a signal to join the meeting and no recording is created.

The correct flow is: prospect or customer receives a Chili Piper scheduling link, books a time, and the resulting calendar event contains the rep's Chili Piper-routed meeting room. Gong reads that calendar event and joins automatically.

See `diagnostics/no-gong-recording.md` for a full troubleshooting checklist.

## Email alias matching

Chili Piper identifies meetings belonging to a rep by matching calendar invitation email addresses against the rep's profile. If a rep has multiple work email aliases (for example, a role-based alias or a legacy address), all of them must be registered in the rep's Chili Piper profile. Unregistered aliases result in invitations that Chili Piper does not recognize, breaking the Gong recording chain.

Reps can add aliases in their personal Chili Piper settings. If they cannot access that setting, file a JIRA RS ticket.

## Ownership and administration

GTM Systems administers Chili Piper org settings, routing rules, and queue configuration. Individual reps manage their own availability windows, buffer times, and meeting types within their personal profile.

## Access

Chili Piper is provisioned by GTM Systems. To request a new seat or to modify routing configuration, file a JIRA RS ticket.

## Routing issues

For unexpected routing behavior (leads going to wrong rep, round-robin imbalance, routing rules not triggering), see `diagnostics/unexpected-routing.md`.

## Documentation maintenance

GTM Systems runs a monthly scan of Chili Piper edge API routing rules to document current expected routing behavior. Changes are PRed to this file. Bump `last_reviewed` on every update.
