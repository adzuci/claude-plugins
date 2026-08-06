# go-jira CLI gotchas

Quirks of the `jira` CLI (go-jira / ankitpokhrel jira-cli) that fail silently or waste round trips. Read this before running any `jira` command in the ticket-for-pr workflow.

## Issue type is immutable after creation

`jira issue edit` has no type flag, and `--custom issuetype=Bug` is **silently ignored**. Getting the type wrong means deleting and recreating the ticket — which needs explicit user approval, breaks any links already made, and burns a key. Decide `Task` vs `Bug` *before* creating.

## Markdown bodies: `--template`, not `-b`

Pass the description via a template/stdin body:

```
jira issue create -t Task -s "<summary>" --template <(printf '%s' "<markdown body>") --no-input
```

Do **not** use `-b $'...'`: a literal `\n` inside a `$'...'`-quoted `-b` string always renders as a forced line break in Jira's markdown renderer, breaking paragraph flow. A template/stdin body is inserted as-is and lets normal markdown line-wrapping work.

Format the body in markdown — headers, lists, code fences as needed.

**The body must contain real newline bytes, not the two-character sequence `\n`.** `printf '%s' "line one\n\nline two"` inside a double-quoted (or single-quoted) shell string does **not** interpret `\n` — it prints the literal backslash-n, which Jira then renders as visible `\n\n` text glued mid-paragraph instead of a paragraph break. Build the body as an actual multi-line value — a `<<'EOF'` heredoc, a real file written with the Write tool, or `printf '%s\n' "para one" "" "para two"` (one `-v`/argument per line, letting `printf`'s own `\n` between arguments do the line-breaking) — then feed that to `--template <(...)` or a file path. Never hand-type `\n` as two characters expecting it to become a line break.

## `edit` does not accept `--template`

Only `create` does. To rewrite an existing description, pipe it:

```
printf '%s' "<body>" | jira issue edit TICKET-NNN -s "<summary>" --no-input
```

## Linking ticket keys inside Jira bodies

Always hyperlink referenced ticket keys — never leave a bare key string. Do this while **drafting the description** (step 3/4), not as an afterthought — the PR-body linking step won't remind you.

The body parser is **markdown**, so use standard markdown links in Jira bodies too: `[TICKET-NNN](<browse url>)`. Never Jira wiki `[text|url]` syntax — that one mangles (leaks literal `[KEY|` and `]` around the link), even standalone at line start when piped to `jira issue edit`.

To verify a link rendered, check the ADF via `jira issue view KEY --raw` — `--plain` output prints a link's display text *and* href, so a correct markdown link looks doubled there and can't be trusted either way.

## Status transitions

```
jira issue move TICKET-NNN "Done"
jira issue move TICKET-NNN "In Progress"
```

Some projects gate transitions (especially to Done) on required fields — resolution, fix version, etc. If the move fails, set the required fields first; project-specific requirements belong in `CLAUDE.md`, not in this skill.

## Capturing the created key

`jira issue create` prints the browse URL on success. Extract the key from it (`.../browse/TICKET-474` → `TICKET-474`) rather than re-querying.

## Lists need a blank line after a heading

A bullet list that starts on the line immediately after a heading loses its **first item** — the item gets absorbed into the heading text (`## Scope* first item`). Put a blank line between the heading and the first `*`:

```
## Scope

* first item
* second item
```

The absorbed-item failure is easy to misdiagnose: only one list in the document tends to show it, and heading level, bold, punctuation, and parentheses are all irrelevant. If a first item goes missing, this is why — don't go hunting for a markup escape.

## Verify rendering with `--raw`, never `--plain`

`jira issue view KEY --raw` returns the stored ADF, which is the only trustworthy check that a body rendered as intended. `--plain` is a lossy terminal rendering: it prints link hrefs alongside display text (see above) and can misrepresent list/heading boundaries, so a `--plain` oddity may be a display artifact rather than a real problem in the ticket. Check `--raw` before restructuring markup to work around something.

There is no `jira api` subcommand for ad-hoc REST calls — `--raw` is the escape hatch. Do not go looking for the API token in config files, env vars, or the OS keyring to curl the REST API directly.

## Epics: `epic create` hangs, use `issue create -tEpic`

`jira epic create -n "<name>" -s "<summary>" -b "<body>"` hangs indefinitely (no output, no issue created). Create epics as a normal issue with an explicit type instead:

```
jira issue create -tEpic -s "<summary>" --template <(printf '%s' "<body>") --no-input
```

## Parent linking: `-P` is a silent no-op, use `epic add`

`-P <EPIC-KEY>` on `jira issue create` does nothing — no error, no issue created at all. Create the child with no parent flag, then link it in a second call:

```
jira epic add <EPIC-KEY> <CHILD-KEY>
```

`jira epic add` works reliably and returns quickly. `jira epic list <EPIC-KEY>` lists an epic's children, useful to confirm the link.

## `issue create` intermittently creates nothing

`jira issue create` sometimes exits with **no output and no ticket created**. Re-running the identical command succeeds. Never infer success from silence — check for the browse URL in the output, and if it's absent, verify with `jira issue list -q "summary ~ <text>"` before retrying.

## Wrap every `jira` call in a timeout

Given `epic create` can hang outright, run `jira` under `timeout 110 …` so one stuck call doesn't consume the whole tool budget.
