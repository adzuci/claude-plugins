---
name: vendor-negotiation-support
disable-model-invocation: true
description: >-
  Helps managers evaluate vendor renewals, pricing, negotiation options, and vendor email
  responses before involving Procurement or Legal.
---

# Vendor Negotiation Support

Help Apollo managers be efficient, pay only for what Apollo needs, and reduce avoidable
workload for Procurement and Commercial Legal. This skill is commercial and operational. It
does not approve contracts, produce legal redlines, or replace Procurement.

## Mode Selection

Infer the mode from the user's words. If multiple apply, run them in this order:

1. `renewals` - discover vendor renewal dates, owners, spend, and next actions.
1. `tldr` - produce a concise manager/Slack-ready deal read.
1. `negotiate` - produce negotiation options, walk-away points, and vendor-facing language.
1. `email` - draft a vendor email response with concise ask math underneath.
1. `handoff` - package evidence and open questions for Procurement, Legal, Security, Finance,
   or the business owner.

Treat explicit arguments such as `email`, `--mode email`, or "draft the vendor response" as
email mode.

Use `/apollo-legal:vendor-contract-review` instead when the user asks to:

- Review whether a contract is okay to sign.
- Redline a PDF/DOCX/MSA/order form.
- Classify a contract into Apollo legal categories.
- Interpret liability, DPA, indemnity, termination, privacy, or legal risk as an approval.
- Scan Ironclad for unreviewed vendor contracts.

If the same request needs both workflows, complete the manager-facing work here first, then
explicitly say what should be handed to `/apollo-legal:vendor-contract-review`.

## Source Packet

Gather real evidence before answering. Prefer primary sources over memory:

- Contract/order form/proposal PDF, screenshots, Gmail thread, Slack thread, Google Drive doc,
  Ironclad or Zip record, Grafana email, spend/usage dashboard, Jira/Notion/Glean context.
- Existing agreement, current annual spend, renewal date, cancellation notice window, payment
  terms, current usage, proposed usage/commit, and internal value story.
- Product/engineering docs showing why Apollo needs the vendor.
- Vendor domain and Apollo company data when negotiating: revenue, headcount, funding, company
  size, and other directional scale signals. Read `references/apollo-cli.md` and
  `references/apollo-data-negotiation.md` when Apollo data could improve leverage or tone.

Check two places before negotiating:

- **Slack, for vendor-named channels** — `#<vendor>`, `#ext-<vendor>*`, `#ext-*-<vendor>`,
  `#tmp-<vendor>-negotiation`, `#ZC:*:<Vendor>`. They hold the live state of the relationship:
  who owns it, what has already been asked, whether Legal is mid-thread. A `#ZC:` channel is
  Zip-created, so one existing means a procurement record probably does too.
- **Apollo CRM, for the vendor as an account** — an open opportunity or customer record means the
  vendor buys from Apollo while Apollo buys from them: a 360 / two-way deal.

Either check can surface the two-way signal. When one does, read `references/360-deals.md` before
drafting any ask.

Keep a source ledger in the output when confidence matters:

```text
Sources checked: <Gmail query>, <Slack thread>, <PDF>, <Glean/Notion/Drive search>, <Zip/Ironclad if available>
Not found: <missing prior order form, owner, usage metric, renewal notice, etc.>
```

Do not invent missing dates, spend, owners, or procurement state.

## Mode: TLDR

Read `references/tldr-mode.md` before writing a TLDR. Default to a Slack-ready note that starts
with the user's requested framing when provided, such as "As I understand the proposal".

Answer the obvious executive math:

- What Apollo pays now.
- What the vendor proposes Apollo commit to.
- Dollar and percentage delta.
- Year-one cash effect versus annualized commitment.
- What business value justifies the delta.
- What is still unverified.

## Mode: Negotiate

Read `references/negotiation-playbook.md`, `references/apollo-data-negotiation.md`, and
`references/multiyear-strategy.md` before writing negotiation options. When the user asks
about how hard to push on discount, term length, ramp-up pricing, use-or-lose credits, or
whether to renew or reopen a competitive process, read `references/multiyear-strategy.md`
first. When the vendor is also an Apollo customer or prospect, read `references/360-deals.md`
and frame the deal as a partnership — help both deals land, never signature for signature.

Always present options, not just one recommendation:

- Default move.
- Best ask.
- Practical fallback.
- Walk-away / pause condition.
- Owner for each next step.

Prefer crisp, respectful vendor-facing language. Make asks concrete enough to paste into an
email or Slack thread.

### When The Deal Is Stalled

Time is the expensive thing, not the last few points of discount. Two unblocks to suggest
whenever a deal or contract goes quiet:

**Find a leadership warm contact.** Check whether Apollo leadership already knows someone at the
vendor — exec-to-exec relationships, board or investor ties, former colleagues. Apollo people
data can surface contacts (see `references/apollo-cli.md`). A warm intro from Apollo's CTO or CEO
to the vendor's VP of Sales or Contracts & Renewals is often the fastest unblock. Spend that
capital on process — legal sequencing, deal speed, named owners — plus one clean commercial ask.
Not on nickel-and-diming.

**Push for a legal-to-legal call.** Propose a live 30 minutes between both legal teams even when
the vendor has not offered it. Redline ping-pong across MSA and DPA rounds burns weeks that one
call resolves. Make the ask concrete: name Apollo's counsel, say their calendars are open, offer
same-day turnaround, and parallel-track the documents instead of holding one hostage to the
other. Fill in the real names and dates from context before sending:

```text
Rather than another redline round, can we put 30 minutes on the calendar with both legal teams
this week? <Apollo counsel name> has open time <days> and we can turn changes around same day.
We'd also like to parallel-track: release the MSA redlines now while DPA review continues, so
the two documents aren't waiting on each other.
```

## Mode: Email

Read `references/email-strategies.md`, `references/apollo-data-negotiation.md`, and
`references/apollo-cli.md` before drafting a vendor response. Use this mode for requests like
"write the email back", "respond to the vendor", `email`, or `--mode email`.

Produce:

1. An email draft that the user can send after light personalization.
1. A short ask math / reasonableness explanation underneath the draft.

The explanation should help the user assess whether the ask is reasonable by comparing current
commit, proposed commit, counter, vendor's possible net ARR, concession requested, Apollo's
usage/value story, and vendor scale signals from Apollo data when available. Cite source and
confidence for Apollo data. Do not run credit-consuming enrichment without user approval.

If Apollo accepts the commercial structure, such as UBB or a three-year term, preserve that in
the email and cut the specific piece that is too high, usually annual commit. Do not make the
vendor think the model itself is blocked when only price is blocked.

## Mode: Renewals

Read `references/renewal-discovery.md` before scanning for renewal dates or vendor inventory.

Use this mode when the user asks to review Grafana emails, find vendor renewal dates, build a
vendor list, identify upcoming renewals, or prepare a procurement calendar. Search Gmail first
when the user mentions emails; use Glean/Drive/Slack/Notion for internal context; use Zip or
Procurement docs when accessible.

Return a table with vendor, product, renewal date, notice deadline, current spend, proposed
spend, owner, source, and next action. If exact values are missing, say `unknown` and name the
source that should resolve it.

## Mode: Handoff

Read `references/procurement-handoff.md` before packaging work for another team.

The goal is to reduce Procurement/Legal workload by doing manager prep:

- Confirm business owner and budget owner.
- Summarize value and usage.
- Identify negotiation asks and source evidence.
- Separate commercial asks from legal/security review items.
- Prep the Zip submission packet and note the expected approval path (see
  `references/procurement-handoff.md`).
- Provide a short handoff note with links and open questions.

Do not create, update, approve, or submit procurement records unless the user explicitly asks
and the relevant connector/tool is available.

## Output Defaults

For a normal manager-facing request, use:

```markdown
## Vendor TLDR
<short Slack-ready paragraph or bullets>

## Numbers
| Item | Value | Source |
| --- | --- | --- |

## Recommendation
<default move>

## Negotiation Options
| Option | Ask | Why | Fallback | Owner |
| --- | --- | --- | --- | --- |

## Handoff / Open Questions
- <Procurement/Legal/Security/Finance/business-owner question>
```

For a narrow Slack wording request, output only the message in a code block.

For email mode, use:

```markdown
## Email Draft
<sendable vendor email>

## Ask Math / Reasonableness Check
- Current vs proposed: <annualized spend, TCV, cash timing, delta>
- Ask: <specific concession and dollar/percent effect>
- Vendor upside: <net ARR vs current and TCV retained>
- Apollo data signal: <vendor scale signal, source, confidence>
- Reasonableness: <why the ask is fair, aggressive, or light>
- Watchout: <risk or concession not to make without owner approval>
```

## Guardrails

- Treat Procurement and Commercial Legal as partners, not blockers.
- Do not claim a contract is approved.
- Do not over-optimize price when the vendor is critical and the value story is strong.
- Separate recurring annual commitment, total contract value, and cash due on signing.
- Use Apollo data as directional negotiation context, not proof of vendor finances.
- On two-way deals, never put signature contingency in writing and keep both deals in their own
  formal approval paths (see `references/360-deals.md`).
- Ask before using enrichment or other Apollo CLI operations that may consume credits.
- Use exact dates, not "soon" or "next month", when renewal or signature deadlines matter.
- Keep manager-facing messages short enough to paste into Slack.
