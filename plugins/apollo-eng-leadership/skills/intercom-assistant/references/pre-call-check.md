# Pre-Call Check

Use this reference for `pre-call-check`: a fast readiness pass before a support rep joins a live call. It is read-only. It produces a checklist and reminders only; it does not start, join, or schedule anything.

Post-Fin context: Fin handles the self-serve layer first, so a live call usually means the issue is non-trivial or the customer wants a person. Read what Fin and the customer already tried before the call so you do not repeat dead ends.

This covers per-call readiness. For per-shift setup (Intercom, Granola, Glean, macros), see `setup-mode.md`; do not restate shift setup here.

## Pre-Call Checklist

- Camera at eye level, framed and lit.
- Headset connected and tested.
- Apollo Admin (GodMode) open in a separate browser tab with the account pre-loaded. GodMode is a web admin you open yourself; there is no automated GodMode lookup.
- Screen share ready on the correct single window, not the whole desktop.
- Notifications silenced; personal tabs and windows closed.
- Full Intercom thread reviewed, including what Fin and the customer already tried.
- Customer data panel reviewed (plan, seats, recent friction).
- Recording disclosure ready to state at call open.
- You can confirm you are speaking with an authorized user on the account (the caller's email matches the GodMode contact). Acceptable forms of identity proof are policy; see `apollo-policies.md`. This file only requires that verification happens.
- `#ama-support-peer-assist` known and staffed in case you get blocked.

## 7-Step Call Framework

1. Welcome: greet, set a helpful tone, and state that the call may be recorded.
1. Verify: confirm both the identity (authorized user on the account) and the concrete issue.
1. Set Expectations: say what you will do, the likely call length, and what happens if it is not resolved on this call.
1. Clarify and Align: ask one concrete question to confirm the goal before troubleshooting.
1. Discovery: gather the specific symptom, recent changes, and account state.
1. Troubleshoot and Guide: work the fix live; narrate what you are doing rather than going silent.
1. Confirm and Close: confirm the outcome, state next steps and owner, and close cleanly.

## Output Shape

```text
Readiness check:
<each checklist item marked ready or not ready, with the gap called out>

Call framing reminders:
<one short reminder per applicable step of the 7-step framework>

Customer + account snapshot:
<who you are calling, plan/seats, the ask, and what Fin/the customer already tried>

Open risks before joining:
<identity not yet confirmed, GodMode not loaded, missing context, or none>
```
