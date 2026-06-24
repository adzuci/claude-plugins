# Research and ERD Reference

Use this reference when an idea is under-specified, ownership is unclear, the observation may duplicate existing work, or an existing ERD may be related.

## When to Use Glean

Call out to the Glean CLI before asking the caller for missing context when any of these are uncertain:

- Product area, likely owner, squad, or existing roadmap context.
- Whether the signal is net-new versus a repeat of an already-known issue.
- Impact, affected segment, or customer pattern when the observation hints at a broader theme.
- The existence of a related ERD, PRD, Jira epic, Productboard note, or decision doc.

If Glean is unavailable or returns no useful result, say that plainly and ask one focused clarification question.

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

## Research Discipline

Use Glean to reduce caller burden, not to inflate the entry. Keep the final idea rooted in the observed support rotation signal. Label unverified inferences, and do not claim an ERD, owner, or Jira relationship unless a retrieved result supports it.
