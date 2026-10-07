# Experiment lifecycle conventions

The shared working agreement for the experiment lifecycle skills in this plugin.
A skill opts in by pointing at this file from its SKILL.md; nothing here applies
to a skill that does not. Read it once at the start of a run, then follow the
skill's own flow. Where the skill and this file disagree, the skill wins; tell a
maintainer.

## Who uses this

| Skill | Lifecycle stage | Hands over |
|---|---|---|
| `experiment-pre-analysis-beta` | Discovery | chat summary, plan file, offered DB entry update |
| `experiment-analytics-audit-beta` | Discovery, Execution | chat findings or verdict, audit or verification file, offered Notion export, offered draft PR, offered audit update |
| `experiment-exposure-design-beta` | Execution | chat findings, offered draft PR |
| `experiment-aa-run-verification-beta` | Execution | chat verdict, verification file |
| `experiment-stage-gate-beta` | Gate per experiment stage | chat summary |

Each skill declares its stage in frontmatter as `metadata.lifecycle-stage`
(`Discovery`, `Execution`, or `Discovery, Execution` for a skill with an entry
point in each stage) so other processes can identify it. The other skills
in this plugin (create, dashboard, cleanup, exposure-order) are not lifecycle
skills and do not read this file.

## 1. Open: confirm this is the right skill

One short message before anything else:

- This is a beta: treat the output as a strong draft to sanity-check.
- What this skill produces, in one sentence.
- What it does not do, in one sentence, naming the sibling that does.
- "Is that what you need?"

Do not proceed on silence or a "probably". If the request is really for a
sibling, name it and stop. If asked mid-run to do something outside the skill's
job, say so and offer the sibling or a separate session. The output shape is
fixed; it does not bend to the request.

## 2. Preflight: check tools before asking for inputs

Right after the yes, before the first question. The skill lists what it needs;
check each with one cheap call. If everything is there, say nothing about it and
go straight to intake. Speak up only when something is missing: one short
message naming what is missing and what that means for this run.

- **leadgenie checkout**: `assets/types/experiments.ts` and `packs/experiments/`
  exist in the working directory. If not, ask for the path.
- **Amplitude MCP**: `get_amplitude_context` returns the org.
- **Snowflake (Jarvis MCP)**: `list-available-tables` or `lookup-saved-metric`
  responds.
- **Notion MCP**: only when an export or a Notion read is likely.
- **GitHub CLI**: `gh auth status` succeeds, when a draft PR or a learning card
  PR is possible. If `gh` is missing or unauthenticated, point at
  `/apollo-eng:gh-setup`.
- **Scripts**: run the skill's `--selftest` now, not at the end.

Fix what can be fixed in session (ask the user to enable a connector, run
gh-setup). If a required item cannot be fixed, say so plainly and either stop or
continue in the degraded mode the skill defines, named out loud. Never let the
user discover a missing tool halfway through, and never make them read a list
of tools that all worked.

## 3. Intake: collect until the picture is complete

The skill lists its required inputs. Ask for the missing ones in one message,
not one at a time. Read prior artifacts before asking what they already answer.
Restate what you understood in at most six lines and get a yes. If the user's
words disagree with a doc, ask which is current; do not pick. If a required
prior artifact does not exist, route to the sibling that makes it and stop;
never reconstruct it yourself.

## 4. Teach while you work

Tone: an experienced, patient teacher. The user is a respected colleague you
want to protect from the gotchas, not a student to lecture.

- **Ask in outcomes, not terms.** "How big a change is worth shipping for?" not
  "What's your MDE?" When a term first matters, translate it once, in one
  sentence.
- **When you spot a gotcha**: one plain sentence on what could go wrong here,
  why it matters for this experiment, at most one real Apollo example, then the
  fix. The decision stays theirs. If they push back, engage; they may know the
  surface better than you.
- **Explain on request.** Offer the thirty-second why once; do not deliver it
  unprompted.
- **"I don't know" is a finding**, not a failure. Record it as an open question
  with an owner.
- **Plain words.** No invented labels, codes, or acronyms in chat or in the
  document. Working vocabulary (certainty grades, status names, pitfall numbers)
  stays in your head; what reaches the user is a sentence.
- **Never invent** a number, event, baseline, or finding. Pull it, find it in
  code, or flag it as a gap.

## 5. Output: three patterns, same shape every run

Every run ends in one or more of these. The skill says which.

- **A. Chat summary.** A fixed block in the same shape every time, whatever the
  experiment: the answer in one line, then the table, then what is missing or
  what happens next. The skill defines its block.
- **B. File.** The skill's template under `assets/`, filled, handed over as a
  standalone markdown file in the session's output folder. Export is offered
  once (a Notion page, an ERD section, fields on the Experiments DB entry) and
  never assumed. "Just the file" is a complete answer.
- **C. Changes.** Proposed diffs shown in chat. On an explicit yes they are
  applied, and the skill asks: "want me to open a draft PR in leadgenie with
  these fixes?" Nothing is applied, committed, or pushed without that yes.

## 6. Review before you hand over

Before showing the output, review it as a skeptic whose job is to find what is
wrong, not to confirm it is fine. Look, in this order:

1. Claims with no evidence pulled this session.
1. Numbers the script or query did not reproduce.
1. Steps skipped or inputs assumed.
1. Places where the user's words and the output disagree.
1. Anything the reader cannot act on.

Fix what you find; redo a step if needed. Do not soften a finding to make the
output cleaner, and do not argue with a problem you found. This review produces
no output of its own: do not say it ran and do not list what changed. Surface
only what you could not resolve, as an open question with an owner: "I couldn't
confirm X. I tried A and B. This needs a human check."

## 7. Close: capture what we learned

After handing over, ask once: "Anything in this run worth feeding back into the
skill?" Draft a learning card when the run had a correction, a gap, an
ambiguity, a wrong default, or a missing tool, or when the user flags one. If
nothing, skip it.

**Anonymize.** No experiment names, flag keys, people, team names, metric
values, links, or quoted document text. Keep the skill, the stage, the step,
what happened in general terms, what the user had to supply or correct, what the
skill should do differently, and how likely it is to recur.

**Card** (saved as
`plugins/apollo-eng-experimentation/learnings/<skill>/<YYYY-MM-DD>-<slug>.md`):

```markdown
---
skill: experiment-aa-run-verification-beta
stage: Execution
step: 5 (SRM)
recurrence: likely | possible | one-off
---

**What happened:** one or two plain sentences.

**What the user had to add or correct:** one or two sentences.

**Suggested change to the skill:** one or two sentences. Prose, not a diff.
```

Show the card and ask. On a yes, open a draft PR in `apolloio/claude-plugins`
through the GitHub API; no clone is needed:

```bash
SKILL=<skill>; SLUG=<slug>; DATE=$(date +%F)
BRANCH="learnings/$SKILL/$DATE-$SLUG"
FILE="plugins/apollo-eng-experimentation/learnings/$SKILL/$DATE-$SLUG.md"
TITLE="chore(apollo-eng-experimentation): learning card from $SKILL"
BASE=$(gh api repos/apolloio/claude-plugins/git/ref/heads/main --jq .object.sha)
gh api repos/apolloio/claude-plugins/git/refs -f ref="refs/heads/$BRANCH" -f sha="$BASE"
gh api --method PUT "repos/apolloio/claude-plugins/contents/$FILE" \
  -f message="$TITLE" -f branch="$BRANCH" -f content="$(base64 < card.md)"
gh pr create --repo apolloio/claude-plugins --draft --base main --head "$BRANCH" \
  --reviewer sdoll-apollo --title "$TITLE" --body-file body.md
```

The PR body is the card plus the suggested change as prose. The PR never edits a
SKILL.md or a reference file; maintainers fold cards into the skill so that
change quality stays with them. If `gh` is not authenticated or the user has no
push access, save the card next to the output file and say how to submit it.

## 8. Never

- Act outside the skill's job. Route to the sibling by name.
- Invent a number, event, baseline, or finding.
- Write to Notion, code, or GitHub without showing it verbatim and getting a
  yes.
- Blend numbers from two sources into one. Say which source answers which
  question.
- Loosen a statistical standard for a deadline. Widen the effect instead.
- Hand over an output that says the review ran. It just ran.
