# Enrich Mode

Use this when the user needs to know who is actually in a deal — on the vendor's side and
Apollo's — and how to reach the vendor-side people. The output is a who's-who a manager can
paste into a brief or a Slack thread, not a prospecting list.

Invocation:

```text
/apollo-legal:vendor-negotiation-support enrich <vendor-domain>
/apollo-legal:vendor-negotiation-support enrich <vendor-domain> #ext-vendor-apollo
/apollo-legal:vendor-negotiation-support enrich <vendor-domain> <pasted names>
```

## Step 1 — Discover Participants

Build the raw roster from what already exists before enriching anything:

1. **Slack**, using the vendor-channel patterns in the Source Packet (`#<vendor>`,
   `#ext-<vendor>*`, `#ext-*-<vendor>`, `#tmp-<vendor>-negotiation`, `#ZC:*:<Vendor>`). Who posts,
   who answers pricing questions, who is looped in for legal or security.
1. **Apollo CRM**, for the vendor account and any open opportunity: AE owner, contacts on the
   record, and anyone tied to the two-way deal (see `references/360-deals.md`).
1. **Pasted names or a deal/channel reference** the user provided.

Split the roster into two lists before enrichment:

| List | Fields to capture |
| --- | --- |
| Vendor side | Name, role in this deal, where you found them |
| Internal side | Name, what to route to them (pricing, legal, security, budget, exec sponsor) |

Only vendor-side people go through enrichment. Internal people come from Slack and CRM context.

## Step 2 — Verify And Enrich Vendor-Side People

Use the Apollo MCP server's prospecting/enrichment tools. Prefer matching by **LinkedIn URL over
name plus domain**. Name plus domain misses people whose Apollo record is stale — in a real deal
run, LinkedIn-URL matching found a Director that name search did not return at all. If the user
has a LinkedIn URL, or a Slack profile or email signature contains one, use it.

Match order per person:

1. LinkedIn URL, when available.
1. Name plus vendor domain.
1. Name plus company name, if the vendor uses multiple domains.

If none of the three return a match, check whether a Slack profile or email signature shows the
person's actual email address, and try matching by that email directly before reporting them as
not found.

Surface for each verified person: title, location, email, phone. Keep the role blurb from Step 1 —
the Apollo title is what the vendor's records say, the role blurb is what they actually do in this
deal, and both are useful.

## Step 3 — Credit Guardrails

Title and location matching is cheap. **Unlocking emails and phone numbers consumes credits**, and
the Apollo agent will ask for confirmation with an exact credit cost before it does.

- Always surface that exact cost to the user and get approval before unlocking. Never approve on
  the user's behalf.
- Unlock the shortest useful list, not the whole roster. Ask who the user actually needs to call.
- Never re-run an unlock for data already revealed in this session — re-check what you already
  have first.
- If the user declines, deliver the who's-who with titles and locations only and say which
  contacts are still locked.

## Step 4 — Report Honestly

Coverage is never complete. Say so plainly:

- List who was **not found** in Apollo. This happens, including for senior execs.
- Flag **stale records** — wrong title, old company, obviously outdated location.
- Flag **DNC-registered phone numbers** and do not suggest calling them.
- Never claim blanket coverage ("all contacts verified") when some lookups failed or were skipped.

## Output

Two compact tables. Keep role blurbs under ten words so the whole thing pastes cleanly:

```markdown
## Who's Who — <Vendor>

### Vendor Side
| Name | Role in deal | Title (Apollo) | Location | Email | Phone | Source |
| --- | --- | --- | --- | --- | --- | --- |

### Apollo Side
| Name | Route to them | Source |
| --- | --- | --- |

**Not found / stale:** <names, and what was wrong>
**Credits used:** <exact cost, or "none — no unlocks approved">
```

Use `unknown` for missing fields and `locked` for contact data the user did not approve
unlocking. Do not guess an email pattern.

## If Apollo MCP Is Not Available

If the Apollo MCP tools are not in the session, say so and tell the user how to enable them:

- **claude.ai** — connect the Apollo connector in Settings → Connectors.
- **Claude Code CLI** — `claude mcp add` with the server at `https://mcp.apollo.io` (OAuth).

Until then, still deliver Step 1: the Slack- and CRM-sourced roster is useful on its own. Use
`references/apollo-cli.md` if the user needs vendor *company* scale data rather than people.
