# LeadGenie Repo Gotchas

Repo-wide facts every agent working in `apolloio/leadgenie` needs. Canonical source is
leadgenie's `CLAUDE.md` (added there by
[leadgenie#97942](https://github.com/apolloio/leadgenie/pull/97942)); this copy exists for
surfaces where that file is not in context. If the two drift, leadgenie's `CLAUDE.md` wins.
Check for drift whenever this skill or the leadgenie `CLAUDE.md` is revised — no automated sync exists.

Last verified 2026-08-07 against LeadGenie `CLAUDE.md` at
[`0503a20`](https://github.com/apolloio/leadgenie/blob/0503a20c8f6d9f56a1d1a98825114ce5820ca93a/CLAUDE.md).

- **Sensitive-file approval gates:** files marked `sensitive: true` in `apollo-dev-teams.yml`
  are `policy-bot`-enforced and need the owning team's Slack approval — a human gate, not a
  fixable CI failure.
- **Pre-push hooks:** `SKIP_PREPUSH_RUBOCOP_CHECK=1` (see `lefthook.yml`) may skip the pre-push
  rubocop hook only after rubocop passes another way (e.g. in Docker); never use `--no-verify`.
