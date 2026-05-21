---
last_reviewed: 2026-05-20
---

# Diagnostic: call not recorded in Gong

> **Processing delay:** Gong may take 5-15 minutes to process a completed call before it appears in the system. If the call just ended, wait and recheck before working through this checklist.

Work through these root causes in order before escalating.

## 1. Personal meeting room URL not used

Was the meeting scheduled using the rep's Chili Piper personal meeting room URL? Any Zoom link that bypasses Chili Piper — whether sent directly by the rep or joined by the external participant — means the Gong recording bot will not join. The meeting must flow through the Chili Piper layer for recording to trigger.

To verify: check whether the calendar event was created from a Chili Piper scheduling link. In Zoom, confirm the meeting is listed under the rep's Chili Piper-associated room by checking **Recording settings → Associated Meeting URLs**.

Resolution: re-book future meetings using the CP personal meeting room link. For the missed recording, file an RS JIRA ticket with the meeting ID, date, and rep name.

## 2. Email alias not registered in Chili Piper

Did the calendar invite come from a non-primary email alias? Chili Piper matches invitations by email address. Common aliases that cause mismatches:

- `a.smith@apollo.io` vs `asmith@apollo.io`
- `@apollomail.io` addresses used in the Apollo email product

To verify: go to the rep's Gong profile at https://us-5287.app.gong.io/my-profile?workspace-id=6673373495655085070&company-id=458243381583341156&hierarchy-id=1 (Apollo-specific URL — update this if workspace IDs change) and check the email addresses listed. Then check their Chili Piper profile to confirm all aliases are registered under **Additional email addresses**.

Resolution: the rep can add missing aliases in their Chili Piper profile settings. Alternatively, file an RS JIRA ticket requesting GTM Systems add the alias.

## 3. Recording consent not set

Is the rep operating in a jurisdiction with recording consent requirements? Gong may require explicit opt-in for markets with two-party consent laws. If the opt-in was never set or was reset during an org change, recordings will be suppressed.

Resolution: file an RS JIRA ticket with the rep name and meeting details.

## 4. Meeting type excluded by org policy

Some meeting types are excluded from recording by default: internal-only meetings (no external participants), and certain categories configured at the org level. If the external participant count was zero, this is the likely cause.

Resolution: if this was an external call that should have been recorded, file an RS JIRA ticket.

## Escalation

For root causes that cannot be resolved by updating the rep's profile directly, file an RS JIRA ticket with:
- Rep name and Apollo email
- Meeting date and time
- External participant email (if known)
- Zoom meeting ID or link
- Which root cause you believe applies
