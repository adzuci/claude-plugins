---
name: leaked-data-verification
description: Analyze a leaked-data sample or proof-of-possession file to judge whether it is fabricated or plausibly real, using record-ID formats, reserved values, and statistical tells. Use when a threat actor sends a data sample, or a dump is claimed to be Apollo data.
disable-model-invocation: true
---

# Leaked Data Verification

> **This skill can prove a sample synthetic. It can never prove one genuine.**
> A well-built fake passes every check here. Only a row-level match against the
> source system establishes possession. Report "fabricated" or "not disproven" —
> never "verified real".

When someone claims to hold Apollo data, the first question is whether they do.
That question is answerable in minutes from the sample alone, before any
production query, and often before Legal needs an answer.

## Usage

```text
/apollo-infosec:leaked-data-verification <path-to-sample>
```

## Before you start

- Work on a **copy**. Preserve the original file and its hash as evidence.
- Do not open attachments from a hostile sender outside a sandbox. Hash first.
- Nothing here requires contacting the sender. Do not reply.

## The four layers

Run them in order. Stop early only on a positive finding — layer 1 disproving a
sample makes layers 2 and 3 unnecessary, but never makes layer 4 unnecessary if
the incident is real.

### Layer 1 — Record ID formats

Real identifiers come from real systems and carry those systems' constraints.
See `references/id-formats.md` for the full table.

```bash
python3 scripts/check_id_formats.py sample.csv \
  --object-id-col APOLLO_TEAM_ID \
  --salesforce-col SFDC_ACCOUNT_ID --entity Account
```

Fast checks:

- **Mongo ObjectId** — 24 lowercase hex, no prefix. Any character outside
  `[0-9a-f]` disqualifies it. The leading 4 bytes decode to a creation
  timestamp; an implausible date is its own tell.
- **Salesforce** — 15 or 18 characters. For 18, the trailing checksum must
  agree with the first 15. The 3-character prefix must match the entity the
  column claims to be (`001` Account, `003` Contact, `00Q` Lead).
- **Snowflake has no row-ID format.** A column claiming Snowflake provenance
  with a uniform synthetic identifier is itself the tell.

### Layer 2 — Reserved values

Standards bodies reserve values that cannot appear in real data.

```bash
python3 scripts/scan_reserved_values.py sample.csv
```

Reserved domains (`.example`, `.test`, `.invalid`, `.localhost`), the NANP
fictional phone range (555-0100 to 555-0199 only — other 555 numbers are
assignable), and RFC 5737 documentation IP ranges. See
`references/reserved-values.md`.

### Layer 3 — Statistical tells

Generated data carries the shape of the loop that made it. See
`references/statistical-tells.md`. The strongest single check:

```bash
python3 scripts/check_id_formats.py sample.csv \
  --correlate APOLLO_TEAM_ID SFDC_ACCOUNT_ID
```

**Cross-column ordinal correlation.** If identifiers from two independent
systems share a trailing counter on most rows, no export produced this file.
Two systems that have never coordinated a counter do not agree on one.

Also: near-uniform category distributions, timestamp granularity clustering,
and sequential IDs where the real system emits non-sequential ones.

### Layer 4 — Match against the source system

Layers 1 to 3 can only disprove. To establish possession you need a row-level
match against the store the data claims to come from.

**Provenance labels are not evidence.** A `Source:` column stating a system
name is a string in a file, not a verified path. Determine the source from the
schema shape, then confirm against the store itself.

**Diff against previously exposed Apollo data first.** Recycled old data is the
most common explanation for a claim like this, and it is the cheapest test
available. Whether a reference copy is retained for this purpose is an open
question — if it is not, say so in the ticket rather than skipping the step.

Route the match query through the team that owns the store.

## Reporting

State findings in this shape:

- **Fabricated** — a value present in the sample cannot exist in real data.
  Give the specific field and why.
- **Not disproven** — the sample survived layers 1 to 3. This is not
  authentication. Say what layer 4 would require.
- **Confirmed match** — a row-level comparison against the source system
  matched. Only this establishes possession.

Two rules for any count that reaches Legal or an executive:

1. **Derive every number from the file in front of you.** Do not copy figures
   from a summary document. A summary and its dataset can disagree, and the
   summary is the one people quote.
1. **Capability and possession are separate findings.** A sample can be
   fabricated while the underlying exposure is entirely real. Disproving the
   sample does not close the incident.

## Related

- `apollo-eng-devops:incident-response` — operational incident command
- `apollo-eng-devops:incident-triage` — Jira INCIDENT and INFOSEC triage
