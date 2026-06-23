# Tech & Product Issues — Reference

> Source of truth: #ama-support-peer-assist channel history + IKB articles
> Last updated: June 2026
> Owner: Tech Support team

______________________________________________________________________

## AI CREDITS & POWER-UPS (most common issue)

### Qualify Contact / Qualify Account auto-enrichment running unexpectedly

- **Root cause:** Auto-enrich was enabled for Qualify Contact/Account AI custom fields. On billing renewal, a background job runs and processes a large contact set, consuming most monthly credits.
- **Resolution:** Walk customer through disabling auto-enrich for those fields. Then evaluate credit courtesy refund.
- **IKB:** Check Zendesk IKB for Qualify Contact/Account disable steps.

### Waterfall enrichment charges unexpectedly

- **Root cause:** Customer enabled Waterfall (usually unknowingly). Credits consumed per enrichment request.
- **Resolution:** Guide customer to turn off Waterfall. Evaluate courtesy credit refund if first time.
- **Reference:** Temporary Credits Exception Guidelines Notion page.

### AI fields in sequence email body/subject consuming credits

- **Root cause:** Customer added AI-generated fields in email steps. Each send triggers a Power-up credit charge.
- **Resolution:** Show customer how to remove AI fields from email steps. Evaluate courtesy credit refund.

### Workflow consuming credits unexpectedly

- **Root cause:** Misconfigured workflow (broad targeting, no filters, no credit caps) running on schedule.
- **Resolution:** This is customer misconfiguration — not eligible for automatic refund. Billing/lead review if customer persists.
- **Note:** Check workflow settings for Intent Signals filter misuse as a common cause.

______________________________________________________________________

## CALLING & DIALER

### Power Calls loading Parallel Calls instead

- Try different browser and incognito first.
- If still reproducible → escalate to Tech as a product bug.

### Advanced Dialer add-on questions / invoice adjustments

- Removing an add-on does not automatically update an already-generated invoice.
- PA cannot modify a generated invoice. Route to Account Advocates to void and regenerate.

______________________________________________________________________

## SEQUENCES & EMAIL

### Sequence emails changed without customer doing anything

- Apollo does not log before/after versions for sequence email changes.
- Most likely cause: customer accidentally clicked "Generate with AI" in the email step.
- Walk them through the step to confirm. No rollback option available.

### Full AI email option missing in Sequences

- Flow: Sequence → Automatic email step → Write with AI → Full AI email → Context → Submit and preview.
- If option not visible on rep's test account either → escalate to Tech as a possible product change or feature flag issue.

### Sequence reply not visible in Gmail but present in Apollo

- Apollo syncs email from the mailbox — if it's in Apollo it should be in Gmail.
- Check customer's Gmail filters, spam folder, and mailbox access (another user may have the mailbox).

### Sequence not triggering / emails delayed

- Apollo has default send delays between steps. Walk customer through sequence timing settings.
- If sequences paused unexpectedly → check deliverability issues or connected mailbox health first.

______________________________________________________________________

## SEARCH & LISTS

### People Search URL now shows unique ID instead of filters

- This is an intentional product change (URL shortening/unique ID system).
- If customer has integrations relying on the old URL format → escalate to Tech to confirm behavior and any workaround.

### Saving contact to list charges credits despite Waterfall toggled off

- Known/potential bug: toggling Waterfall off in the bulk save modal may not prevent email exposure in all cases.
- Steps to replicate: select 2+ net new contacts → Save → bulk save modal → toggle Waterfall off for email → Add to list → Save.
- Expected: no email exposure/credit charge. Actual: email exposed and credits charged.
- Escalate to Tech as a bug with replication steps.

### Deleting a saved search — no delete button visible

- Delete button only appears for searches the user created themselves.
- If created by someone else (e.g., a PS during onboarding), user cannot delete it.
- No known admin override. Confirm with Tech if a workaround exists.

______________________________________________________________________

## API & INTEGRATIONS

### API rate limit increase (contacts/search endpoint)

- `/api/v1/contacts/search` can be increased to 5,000/day by PA without needing `#ray-requests`.
- Reference: *Raising API Limits* Notion page for current thresholds and other endpoints.

### Legacy plan API credit usage

- Legacy plans use Export credits for most API endpoints.
- If team has no Export credits, confirm whether the specific endpoint actually consumes credits (some don't).
- Reference IKB: *Apollo API Credit Usage and Rate Limits*.

### Contacts not syncing to Snowflake via Fivetran

- When contacts are added to a sequence, `updated_at` may not change → Fivetran sync not triggered.
- This is a tech-level issue → escalate to Tech Support.

### Apollo ↔ Salesforce email activity not syncing

- Check if there is an existing CETS escalation for the account.
- Escalate to Tech with the CETS link if available.

______________________________________________________________________

## ACCOUNT & ADMIN

### Admin no longer with the company — account access

- After identity verification: if ≤10 days + \<10% usage (M2M) or \<5% (annual) → PA can proceed.
- Transfer of ownership is an option. Reference billing policy for steps.

### Sub-account wants to separate from Parent team

- Requires manager approval.
- IKB: *Convert a sub-account to a stand-alone account*.
- The "Delete" option in Apollo admin removes the sub-account relationship — confirm exact behavior before using it.

### VM drop recordings disappeared

- Phone number deletion (after 2 months of inactivity) may remove associated VM drop recordings.
- No known recovery method beyond re-recording.
- Confirm with Tech if any recovery path exists.

### Support access / privacy concern (customer saw agent in their account)

- Do not confirm or deny specific session details without a privacy/security review.
- Escalate to Privacy or Security team. They will review JIT access logs.
- Do not classify as a Security Incident without review.

______________________________________________________________________

## BILLING SYSTEM ISSUES

### Payment processed but plan still shows Free

- Confirm payment in Stripe first.
- If confirmed → escalate immediately as high-impact billing/tech issue. Use *Billing Escalation Follow-Up* workflow.

### Customer paid but plan processing stuck

- High urgency. Use *Billing Escalation Follow-Up* workflow in `#ama-support-peer-assist`.

### Customer wants to void open invoice to switch to annual plan

- If current invoice is blocking an upgrade → route to Billing / Account Advocates to void and allow re-purchase.

### Invoices missing from Apollo invoice history (available in Stripe)

- Use *Stripe Information Request* workflow in `#ama-support-peer-assist` to request PDF copies from Stripe.

### Invoice reissue under different legal entity

- Voiding paid invoices is not standard. Requires Billing Ops review.
- A credit memo + corrected invoice reissue may be possible — Billing Ops decides.
- Escalate with full invoice details and correct legal entity info.

______________________________________________________________________

## FEATURES & PLATFORM

### UK mobile numbers not available in account

- PA cannot assign Twilio numbers. This requires Tech Support to provision from Twilio.
- Escalate to Tech.

### Record selection limit — customer seeing 1,000 instead of 10,000

- This is a plan variant issue (split pricing). The customer may be on a variant (e.g., AB59) with a 1,000-record limit.
- IKB: *Change Plan Pricing Variant*. Note: AB59 and AC59 are the only variants a team can be changed to.
- If customer wants to cancel because of this → evaluate under misunderstanding/capabilities refund scenario.

### AI Assistant giving wrong info (e.g., 25-record limit on paid plan)

- Paid plans support up to 2,500 net new contacts and up to 50k saved contacts.
- If customer is requesting a refund because of AI misguidance → evaluate under misunderstanding/capabilities refund scenario.

### Customer on new sequence UI (feature flag) wants old UI

- If the new UI is behind a feature flag (e.g., `sequenceEmailsFinderV2Enabled`) and rollout is imminent, generally do not revert.
- Use judgment: if it's causing a material workflow blocker and rollout is weeks away, Tech can disable the flag temporarily.

### Apollo promoted a third-party offer (e.g., Perplexity) and customer was charged

- Apollo is not responsible for charges by third-party partners.
- Escalate to Partnerships/BD team to resolve directly with the partner.
- Do not issue a refund from Apollo's side for third-party charges.
