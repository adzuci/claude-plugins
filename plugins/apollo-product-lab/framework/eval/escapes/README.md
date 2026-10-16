# Escape records and replay fixtures

An escape is a finding on a harness artifact, after a gate passed, that changed the approach or
found a defect (doc 43 §2). Each adjudicated escape gets one record here, written by
`/harness-escape fix <escape-id>`.

## Record shape

One file per escape, `<yyyy-mm-dd>-<slug>.md`, with this frontmatter and these sections:

```yaml
id: <initiative>-<n>
kind: replay | retrospective   # retrospective = the originals were not archived
initiative: <slug>
artifact: <PR number, snapshot file name or Notion page title>
owning_stage: <A.audit | C.specify | D.design | E.review | F.build | G.verify | council.<kind>>
adjudicated_by: <role, for example "initiative EM">
adjudicated_on: <date>
fix: <platform-rules.md row, lens checklist row, or check name>
```

- **Finding**: what the reviewer found, in plain words.
- **Owning stage**: the stage whose declared job covered it, and the evidence it had at the time.
- **Why it was missed**: one of: missing knowledge; existing path not found; rule existed but was
  not applied; no lens for this.
- **Fix**: what changed, with a link to the rule, row or check.
- **Replay**: for `kind: replay` only. The fixture directory `<id>/` holds the original artifact
  bytes, the repo revision, the evidence, the instructions, and the model and tool settings. Report
  the result on the defective case, its corrected version and one held-out variant; for a model
  check, 3 runs with detection and false-alarm counts.

A record without archived originals is `kind: retrospective` and says "retrospective case, not
replay". It is a lesson, not evidence that the fix works.

## Records

| Id | Kind | Owning stage | Fix |
|---|---|---|---|
| [campaigns-merge-tag-fallbacks-1](./2026-10-06-merge-tag-fallbacks.md) | retrospective | E.review (architecture and backend lenses) | doc 43 §4, §5; platform-rules R6 |
| [ads-builder-erd-1](./2026-10-06-ads-erd-platform-knowledge.md) | retrospective | E.review (architecture lens) | platform-rules R1 to R5; worked examples |
| [ads-builder-hook-cost-1](./2026-10-12-ads-hook-host-path-cost.md) | retrospective | E.review (infra lens, Load model) | IP18; doc 17 §6.2; doc 34 infra lens; doc 21 §8c |
