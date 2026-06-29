# Research and ERD Reference

Use this reference when an idea is under-specified, ownership is unclear, the observation may duplicate existing work, or an existing ERD/PRD may be related.

## When to Use Glean

Call out to the Glean CLI before asking the caller for missing context when any of these are uncertain:

- Product area, likely owner, squad, or existing roadmap context.
- Whether the signal is net-new versus a repeat of an already-known issue.
- Impact, affected segment, or customer pattern when the observation hints at a broader theme.
- The existence of a related ERD, PRD, Jira epic, Productboard note, or decision doc.

If Glean is unavailable or returns no useful result, say that plainly and ask one focused clarification question.

## When PRD Lookup Is Worth It

Do a PRD lookup when the idea sounds like it may overlap planned product work, not for every idea.

Look for related PRDs when any of these are true:

- The observation names a product surface, workflow, or feature that is likely roadmap-owned.
- The suggested next step is product discovery, UX change, new automation, or a product enhancement.
- The issue may already be covered by a PRD, one-pager, roadmap item, ERD, Jira epic, or Productboard note.
- The entry would be more actionable if it linked to existing product intent or a likely owner.

Skip PRD lookup when the signal is clearly support-process-only, billing/account-administration-only, a one-off customer education issue, or already has a specific approved ERD/Jira link. In those cases, avoid spending tokens on broad product search.

If uncertain, do one local cache search first. Only run live Glean if the cache is missing, stale, or has no plausible hit.

## Local PRD Cache

Use the local PRD cache before broad Glean PRD searches. The cache stores only PRD/one-pager titles, URLs, and short TLDRs so repeated support shifts do not re-read large docs.

Default cache path:

```text
~/.cache/apollo-skills/add-support-rotation-idea/prd-title-cache.json
```

Check freshness:

```bash
python3 scripts/prd_cache.py status
```

Search the cache:

```bash
python3 scripts/prd_cache.py search --query "<product area> <core problem terms>" --limit 5
```

Refresh the cache only when it is missing or more than 7 days stale:

```bash
python3 scripts/prd_cache.py refresh
```

After a cache hit, open at most the top 1-2 candidates and only when the title/TLDR matches the same product surface and customer problem. If cache results are weak, do not force a link; mention the strongest candidate as possible adjacent context only if useful.

## Glean CLI Commands

Prefer small, targeted searches and inspect titles, URLs, and snippets before opening anything deeper.

```bash
glean search --page-size 5 --fields results.document.title,results.document.url,results.snippets "<product area> <core problem terms>"
glean search --page-size 5 --fields results.document.title,results.document.url,results.snippets "\"<idea phrase>\""
glean search --page-size 5 --fields results.document.title,results.document.url,results.snippets "<product area> <core problem terms> ERD"
```

Use `--return-llm-content` only when a result looks relevant and the summary/snippet is not enough:

```bash
glean search --page-size 3 --return-llm-content "<product area> <core problem terms> ERD"
```

## ERD Linking Rule

Search for an existing relevant ERD before creating the idea. Treat an ERD as definitely related only when the title, snippet, or opened content matches the same product surface and the same user/customer problem or implementation area.

- If exactly one ERD is definitely related, ask the caller before linking it: "I found a likely related ERD: <title>. Do you want me to link it in the idea?"
- If multiple ERDs look related, list the top candidates and ask which one to link.
- If candidates are weak or adjacent only, do not ask for approval as if they are related. Mention the strongest candidate in the recap as "possible adjacent context" only when useful.
- If the caller approves, include the ERD URL in `Related context` or the closest matching Notion property returned by the database schema.
- If the caller does not respond and the entry is otherwise urgent, draft without the ERD and note that the link is pending caller approval.

## PRD Linking Rule

Treat a PRD as related only when the cached title/TLDR or opened content matches both the affected product surface and the observed customer/support problem.

- If one PRD is a strong match, ask the caller before linking it: "I found a likely related PRD: <title>. Do you want me to link it in the idea?"
- If multiple PRDs look related, list the top 2-3 titles with one-line TLDRs and ask which one to link.
- If matches are weak, do not ask for approval as if they are related. Mention the strongest match in the recap as "possible adjacent PRD" only when useful.
- If the caller approves, include the PRD URL in `Related context` or the closest matching Notion property returned by the database schema.
- If the caller does not respond and the entry is otherwise urgent, draft without the PRD and note that the link is pending caller approval.

## Apollo Engineering Teams

For the canonical team list and ownership mapping, read `references/engineering-teams.md`.

## Research Discipline

Use Glean to reduce caller burden, not to inflate the entry. Keep the final idea rooted in the observed support rotation signal. Label unverified inferences, and do not claim an ERD, PRD, owner, or Jira relationship unless a retrieved result supports it.

Use the cheapest evidence path first:

1. Local PRD cache title/TLDR search.
1. Small Glean search by product surface and core problem.
1. Open only the top 1-2 promising docs.
1. Ask one focused clarification question if the evidence is still weak.
