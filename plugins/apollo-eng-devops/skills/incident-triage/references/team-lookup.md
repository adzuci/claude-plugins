# Team Lookup: Identity, Ownership, and Renames

The skill never hardcodes team names. It resolves ownership at runtime from two canonical sources, and degrades gracefully when they disagree.

## Canonical sources

1. **`apollo-dev-teams.yml`** — the authoritative list of currently-active teams.
   - Raw URL: `https://raw.githubusercontent.com/apolloio/leadgenie/master/apollo-dev-teams.yml`
   - Companion doc: <https://github.com/apolloio/leadgenie/blob/master/.windsurf/rules/apollo-dev-teams.md>
   - Treat any team slug not present here as **unknown** — never guess.
1. **`CODEOWNERS`** in the repo that produced the finding — the authoritative path → team mapping.
   - Fetch via `mcp__github__get_file_contents` from the repo's default branch at `.github/CODEOWNERS`, `CODEOWNERS`, or `docs/CODEOWNERS` (try in that order).
   - Apply standard CODEOWNERS rules: later patterns override earlier ones; longest-match wins on a tie.

## Identity resolution (who is "me"?)

The skill needs the set of team slugs the running user belongs to. Try in order, stop at the first that returns a non-empty set:

1. **Skill argument or saved preference.** If the user invoked with `--team=<slug>` or there's a session value, use it.
1. **Atlassian identity → registry cross-reference.** Call `atlassianUserInfo` to get the user's email. Fetch `apollo-dev-teams.yml` and look for the email in any member/lead field the schema exposes (read keys dynamically — do not assume `members:` is the field name).
1. **GitHub identity → team membership.** Call `mcp__github__get_me` then `mcp__github__get_teams`. Intersect the returned `@apolloio/<slug>` teams with the slugs known to the registry.
1. **Ask the user.** Present registry-known slugs via `AskUserQuestion` (multi-select). Offer to remember the answer for the session.

Multiple memberships are normal (managers, on-call rotation, dual-hat ICs). The skill treats the union as "mine."

## Path → team resolution

For each affected path in a finding:

1. Identify the repo. Sources expose this differently — see `finding-sources.md`.
1. Fetch CODEOWNERS for that repo.
1. Match the affected path against CODEOWNERS rules.
1. Extract the `@apolloio/<slug>` owner from the matched line.
1. Validate the slug against `apollo-dev-teams.yml` (next section).

If the repo has no CODEOWNERS file, flag it as a hygiene issue in the proposed comment and route as `?`.

## Validating a slug against the registry (rename handling)

After CODEOWNERS produces a slug, check it against the registry. Three outcomes:

1. **Slug is in the registry → use it.** Read its display name, Slack channel, lead handle, etc. dynamically from whatever fields the YAML defines. Do not bake field names into the skill.

1. **Slug is not in the registry → try fallbacks in order:**

   a. **Alias / former-name lookup.** Read each registry entry and check any field that could plausibly hold aliases: `aliases`, `previous_names`, `former_slugs`, `also_known_as`, etc. Match the CODEOWNERS slug against those. If a unique match is found, use it and add a note to the proposed comment: "CODEOWNERS in `<repo>` still references the former slug `<old>`; the team is now `<new>` per `apollo-dev-teams.yml`."

   b. **Fuzzy match.** Compute Jaccard similarity over slug tokens (split on `-`). If exactly one registry slug scores ≥ 0.7, use it and prefix the proposed comment with "Did you mean `<match>`?" — leave the final call to the human.

   c. **Give up.** Mark the row as `?` with the hygiene note: "CODEOWNERS in `<repo>` references `@apolloio/<slug>`, which is not in `apollo-dev-teams.yml` (no alias match, no fuzzy match ≥ 0.7). Either the team was renamed and CODEOWNERS is stale, or the registry is. Do not auto-reroute."

1. **CODEOWNERS line returns multiple owners.** Treat all of them as "co-owners." If any one of them is in the user's team set, classify as KEEP. Otherwise propose a reroute to the first co-owner and mention the others in the proposed comment.

## Caching

Fetch `apollo-dev-teams.yml` and any CODEOWNERS files **once per session** (preflight) so a triage run is internally consistent. **Never cache across sessions.** Renames must propagate the next time the skill runs.

## What the skill must never do

- Hardcode a team slug in any reference file or comment template (templates use placeholders populated at runtime).
- Write a team slug into a Jira custom field that would need migration on a rename.
- Auto-correct a CODEOWNERS/registry mismatch silently. Mismatches are flagged for humans.
- Assume the registry schema. Field names are read dynamically; missing fields degrade to "not available" rather than crash.
