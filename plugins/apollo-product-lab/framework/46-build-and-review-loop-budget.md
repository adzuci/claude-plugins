# 46. Build and review loop budget: run less, run it once, and report the minutes

> Why (Akansh, 2026-10-09): six small review fixes on one Rails PR took 3.9 hours, about 466k agent
> tokens and about 680k cross-family review tokens. About 1 h 50 min went to build, tests and about 30
> mutants before the first review. Four Astra xhigh passes took 5 to 11 minutes each. About 1 h 30 min
> of fix loops re-ran the full suite (about 1,000 examples) and every mutant after each fix. Every spec
> run started a fresh container (`docker run --rm`) with `RSPEC_CREATE_MONGO_INDEXES=1`, so each paid a
> cold Rails boot and an index build. The first review prompt was 59k characters. None of that time
> showed up anywhere a person could see it.

Terms used below:

- **Affected specs**: the specs a change can break, picked by test-impact analysis (in leadgenie, the
  `ci-speed-run` skill) rather than by running everything.
- **Mutant**: a deliberate small break in the production code (flip a condition, drop a call) used to
  prove a test fails when the behaviour it claims to cover is broken.
- **Cross-family review pass**: one review of the change by a model from a different family than the
  author (doc 43, doc 34 §3), for example Astra xhigh through `codex exec`.

These rules bind every slice owner (doc 20 §4), every fix loop after review, and every cross-family
review the council or a build runs. They are defaults; a human may lift any of them for one run, and the
stage snapshot records who and why.

## 1. Test loop: reuse the running app

1. Run specs in the app container that is already running (`docker exec` into the existing dev
   container), never a fresh container per run (`docker run --rm` pays a cold boot every time).
1. Rebuild database indexes only when an index definition changed in this change. Otherwise do not set
   the index-creation flag.
1. The exact commands come from the target repo's `CLAUDE.md` and skills, not from this doc. For
   leadgenie: `SKIP_COVERAGE=1 bin/rspec <files>` inside the running rails container,
   `RSPEC_CREATE_MONGO_INDEXES=1` only on the first run after an index change, and the `ci-speed-run`
   skill for affected-spec selection.
1. No running container: start the repo's dev container once and reuse it for the rest of the run.

A type check and a spec run in the same app container at the same time can crash the runtime and leave
a core dump over tracked files (seen on a past Ads M1 build with `srb tc` and `bin/rspec`): run them one
after the other, and restore any tracked file a crash overwrote.

## 2. Affected specs while iterating, the full suite once

1. During build and every fix loop, run only the affected specs (test-impact selection).
1. Run the full relevant suite (the packs or packages the change touches, plus the repo's always-run
   guards) **once**, before the commit that goes to review.
1. Fix loops after a review run affected specs only. The fixes then get one more full-suite run, before
   their commit. Any other full-suite run is a budget breach; record it in the loop report (§6).

## 3. Mutation checks: once, at the end, at most 10

1. Run mutants once, after the code is final for this round, not during build and not after every fix.
1. Only on behaviour changes: no mutants for renames, copy, config moves or test-only changes.
1. Target 10 mutants or fewer. Pick the conditions and calls a reviewer would ask about first. More
   than 10 is a named breach in the loop report (§6), with the reason.
1. Run each mutant against its own spec file only, not the suite.
1. After a fix, re-run only the mutants whose mutated lines the fix changed. A mutant on untouched code
   keeps its earlier result.

## 4. Cross-family review: two passes, then a human

1. **Pass 1** reviews the full change.
1. **Pass 2** reviews the delta only: the fixes made in answer to pass 1, with pass 1's findings as the
   question.
1. **If pass 2 still has blockers, stop.** Do not run a pass 3. Return to the human with options (for
   example: accept with a named follow-up, rework the approach, or ask for one more pass), each with its
   cost in minutes and tokens.
1. Exception: a human explicitly asks for another pass. Record who asked in the stage snapshot.
1. This cap is per artifact (one design, one PR). It counts every cross-family pass on that artifact,
   whatever route ran it (`codex exec`, `council-adversary`, `/codex:adversarial-review`). The
   cross-family lenses of one round (the adversary and, on backend code, `infra-lens`) run in parallel
   and together are one pass; in pass 2 each reads only the delta.
1. A fallback run that stands in for an unreachable reviewer takes that pass's slot; it does not add a
   pass.

## 5. Review prompt budget: the diff, the question, pointers

1. A review prompt holds the diff (for pass 2, the delta), the specific question, and pointers to files
   by path and line. The reviewer has repo access and reads the files itself.
1. No pasted file bodies. Quote at most a few lines when a pointer alone would be ambiguous. The check
   lines a lens must apply (for example the IP rows of doc 44 §5) are part of the question, not file
   bodies, and may be pasted.
1. Target 15,000 characters or fewer. A prompt above that says in its first line why, and is a named
   breach in the loop report (§6). When the diff alone is larger, give `git diff <range>` as a command
   and the file list instead of pasting it.
1. Log the prompt size and the tokens in the ledger for every pass:
   `append.py ... --prompt-chars <wc -c of the prompt> --tokens <n> --minutes <m>`.
1. Excerpt-only routes (Glean, `--tools ''`) are the exception: they cannot read the repo, so they get
   the excerpts they need, still within the 15,000-character target (chunk above it), and are tagged
   `excerpt-only` (doc 34 §3).

## 6. Loop report: make slow loops visible

Every build, fix or council stage snapshot carries one line under **Loop report** (template
`templates/stage-snapshot.md`):

```
Loop report: build <m> min · tests <m> min (<n> runs, <k> full) · mutation <m> min (<n> mutants) · review <m> min (<n> passes, <tokens> tokens, <chars> prompt chars) · fix-loop <m> min (<n> loops) · total <m> min, <tokens> tokens
```

1. Minutes are wall-clock, measured from tool timestamps, not estimated.
1. A breach of §1 to §5 is named on the next line with its reason (`breach: full suite in fix loop 2, because ...`).
1. The report goes to the human with the stage, not only into the file, after the stage-end summary of doc 49 §2.

## 7. Where these rules are wired

| Rule | Carried by |
|---|---|
| §1, §2, §3 | doc 20 §4 and §8d, `harness-intake` engineer path, `product-orchestrator` slice briefs |
| §4, §5 | doc 17 §6.3, doc 34 §4, doc 43 §6, doc 44 §3, `harness-council` steps 3a and 3a-bis, the pr, design and erd kinds |
| §6 | `templates/stage-snapshot.md`, `harness-snapshot` write mode, ledger `--minutes` and `--prompt-chars` |
