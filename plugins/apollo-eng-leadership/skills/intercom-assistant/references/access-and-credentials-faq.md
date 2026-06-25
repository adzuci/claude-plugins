# Access And Credentials FAQ

Use this reference in `live`, `monitor`, and `triage` for login failures, SSO configuration, locked accounts, and seat management. It is read-only: verify and route; do not reset, unlock, or change access.

Post-Fin context: Fin handles the simple "how do I log in" cases, so a human on an access thread usually needs the account state checked or a routing decision. Lead with what to verify, not with a help-center link.

## Hard Stop First

Account takeover often masquerades as "I'm locked out." Before helping anyone regain access, confirm the requester is an authorized user on the account (email matches the GodMode contact). If the access pattern looks suspicious (new device, unusual location, multiple failed attempts, a request to change the recovery email), route to security or fraud per `routing-and-macros.md` and do not self-serve.

## Common Cases

- **Password or login failure**: confirm the account exists and the user is authorized in GodMode, then point to the standard reset flow. Do not reset on the customer's behalf.
- **Locked account**: identify why it locked (failed attempts, billing, ToS/blockage). Billing or blockage locks route to those teams, not to a simple unlock.
- **SSO configuration**: basic questions are answerable; anything that changes the identity provider or domain settings is an admin/IT action. Route to the customer's admin or to the technical queue.
- **Seat management**: adding, removing, or reassigning seats is an account-admin action. Confirm the requester is an admin before guiding the change.

## Guardrail

Read-only. Verify identity and account state, then suggest the route. Do not unlock, reset, change SSO, or move seats yourself.
