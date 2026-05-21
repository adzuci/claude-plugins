---
last_reviewed: 2026-05-20
---

# Diagnostic: Zoom recording not appearing in Apollo

Work through these root causes in order.

## 1. Gong didn't record the call

Apollo processes Gong recordings, not raw Zoom recordings. If Gong never captured the call, Apollo has nothing to process. Check `diagnostics/no-gong-recording.md` first and confirm the recording exists in Gong before continuing.

## 2. Processing delay — less than 1 hour

Gong-to-Apollo sync typically completes within ~15 minutes (SLA: under 1 hour). If it has been less than one hour since the call ended, wait before assuming there is an issue.

## 3. Gong-to-Apollo integration delay or pause

If a recording is in Gong but hasn't appeared in Apollo after 1 hour, the Gong-to-Apollo sync may be delayed or temporarily paused. This is not visible to end users.

Resolution: file an RS JIRA ticket with the call date, Gong recording link, rep name, and external participant email. GTM Systems will check the sync status.

## 4. No matching contact record in Apollo

Apollo attempts to match the call to a contact record using the external participant's email address. If the external participant's email does not exist as a contact in Apollo, the call may process but appear under "unmatched calls" rather than on a specific contact record.

Resolution: create or find the contact record in Apollo, then link it manually to the call. If the email exists but the match didn't happen, file an RS JIRA ticket.

## Escalation threshold

File an RS JIRA ticket if:
- The recording is confirmed in Gong AND
- More than 1 hour has passed AND
- The call still does not appear in Apollo

Include: call date, rep name, Gong recording link (if available), and the external participant email address.
