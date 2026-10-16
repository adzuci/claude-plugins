# 54: Rule Registry and Lifecycle

The review rule registry is `framework/rules/registry.yml`. It is the learning loop's state. Each row
names the rule, its reviewer, lifecycle status, source evidence, and replay evidence. Sources are human
review comment URLs or `seed`. A learner may propose a change. It never edits this registry or a
reviewer prompt by itself.

## Lifecycle

- `candidate`: proposed from a human review comment. It is not in an agent prompt.
- `shadow`: present in the agent prompt. Its findings carry `shadow: true`. `pr-ready` reports them as
  information and never blocks or warns on them.
- `active`: normal review and `pr-ready` tiering apply.
- `retired`: absent from the prompt. The registry keeps the rule and its retirement reason.

Every finding cites a registered rule id. An unregistered id is a record-validation warning. Prompt and
registry consistency is tested: each prompt rule is registered, shadow and active rules are in their
named prompts, and candidate and retired rules are absent.

## Evidence and Changes

A shadow rule may be proposed for promotion only when all of these are true:

- at least three replay cases;
- recall of at least `0.60` on those cases;
- a false-positive rate of at most `0.15` on declined cases;
- a paired probe where the rule-on run has more hits than the rule-off run.

Both runs must contain every declared reviewer output and score the same positive and declined cases.
At least one declined case is required. A missing output or missing negative case is incomplete evidence,
not a zero false-positive rate.

An active rule may be proposed for retirement after zero hits in each of the last three scored replays,
or when its false-positive rate exceeds `0.30`.

Prepare a removal experiment without calling a model:

```bash
python3 scripts/rule-probe.py prepare --rule B46 --out /tmp/B46-probe
```

Run the generated on and off briefs through the same reviewers, then score their replay result folders:

```bash
python3 scripts/rule-probe.py score --rule B46 --on /tmp/B46-on --off /tmp/B46-off
```

The result is `framework/rules/probes/B46-<date>.json`. Generate a human-reviewable proposal and registry
patch with `python3 scripts/rule-promote.py`. After approval, a person runs it again with
`--apply-registry`. That flag changes only `registry.yml`. Prompt edits are always manual.
The applied registry row records the scored cases, hits, false positives, and score date from the probe.

Replay counts are evidence-bound. `cases` counts fixed or deferred corpus cases mapped to the rule.
`hits` changes only after a scored replay. Seeded `false_positives` counts declined corpus cases mapped
to the rule; a scored replay replaces it with the declined cases actually flagged. `last_scored` records
the score date. Missing evidence never counts as a pass.
