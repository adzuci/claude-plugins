# 41 — Where the harness lives, and how several people use it on one initiative

> Decision 2026-09-20 (Akansh). Until now the framework, the skills and the Ads artifacts were untracked
> files on one laptop. That is fine for one person and wrong for a pod of four or five engineers, a PM
> and a designer working on the same product.

## 1. Two homes, by what the file is about

| What | Lives in | Why |
|---|---|---|
| The framework: docs 12–41, `models/`, `templates/`, `ledger/` tooling, `reviews/`, the harness skills (`harness-onboard`, `harness-council`, `harness-snapshot`, `product-harness-init`, `design-diff`, `artifact-audit`, `slice-fit`) and the harness agents (`product-orchestrator`, `council-adversary`, `council-synthesizer`, `slice-contract-keeper`, `slice-integrator`, `product-reviewer`) | `apolloio/claude-plugins`, plugin **`apollo-product-lab`** | It is not about any product. One install gives every host the same version; release-please versions it; the marketplace already reaches Codex too. |
| A product's or feature's artifacts and owners: `.ai/<initiative>/**` (knowledge files, runs, snapshots, ledger, ERD, design gaps) and its domain agents `.claude/agents/<initiative>-*.md` and any product-specific skill | the product repo (`leadgenie`) | They change with the product, are reviewed with the product, and the file-ownership check gives them a team. |

A skill inside the plugin refers to its own files as `${CLAUDE_PLUGIN_ROOT}/framework/...` and
`${CLAUDE_PLUGIN_ROOT}/skills/...`. A product repo keeps a one-paragraph
`${CLAUDE_PLUGIN_ROOT}/framework/README.md` pointing at the plugin so old links still resolve to something.

## 2. Solo or team: the onboarding question

`/harness-onboard` asks it and writes `collaboration: solo | team` into the profile. Solo changes
nothing. Team turns on the sync rules below in every harness skill.

## 3. Git sync rules for a team initiative

One script applies them, so no skill carries its own git incantation: `scripts/record-sync.sh pull <initiative>`
before any read of the record and `scripts/record-sync.sh push <initiative> "<message>"` after any write.
It reads `collaboration:` from the profile and is a no-op for solo. Every skill that writes to
`.ai/<initiative>/` calls it (snapshot, council, decide, intake, init, design-diff, audit); the
orchestrator and the session-start hook pull. The stage is not done while the push has not landed.

1. **Pull before you read.** `harness-snapshot read`, the council and the router run `git pull --rebase`
   on the product repo before opening any snapshot. Someone else's newer snapshot is the record.
2. **Commit and push after every write to the record.** A snapshot, an index row, a ledger event, a
   decision record or a knowledge-file log entry is followed by `git add .ai/<initiative> && git commit && git pull --rebase && git push`. The stage is not done while the push has not landed; a failed push
   is reported, never retried silently with `--force`.
3. **The ledger is append-only, so conflicts are trivial:** on a rebase conflict in `ledger.jsonl` keep
   both sides in timestamp order. `index.md` conflicts are resolved by re-listing the files on disk.
   Snapshots never conflict because nobody edits an existing one (doc 33).
4. **One run per feature, many people per run.** Two people on the same feature share
   `runs/<initiative>-<slug>/`; each stage snapshot names its `produced_by` person and model.
5. **Branch discipline is the product repo's.** Artifacts ride on the feature branch that carries the
   code, or on a dedicated `<ticket>/harness-artifacts` branch when the code has not started; they merge
   with normal review. Nothing in `.ai/` is pushed straight to master.
6. **Never commit a secret or an identifier hash** into `.ai/`; the snapshot rules already forbid it.

## 4. What this replaces

- Untracked `${CLAUDE_PLUGIN_ROOT}/framework/` and `.claude/skills/harness-*` in leadgenie: superseded by the
  plugin. The leadgenie copies are removed once the plugin PR merges and `claude plugin install apollo-product-lab@apollo-plugins` is in doc 39's table.
- Astra finding ENG12 ("any host" not demonstrated): the plugin is the distribution; the cold-start proof
  is one fresh clone of leadgenie plus the plugin install, run through `/harness-onboard` and
  `/harness-snapshot read ads-builder ads-m1-run1`.
