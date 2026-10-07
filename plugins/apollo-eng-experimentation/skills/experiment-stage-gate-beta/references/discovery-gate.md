# Discovery gate: the five items

The gate from Discovery into Execution, as the Growth Experiment Lifecycle
Framework defines it. Each item is a thing the team should know and have
written down somewhere; where it is written is the team's business. The
"What this means" and "Complete when" text under each item is read to the DRI
as written, so it stays the same from run to run.

## Artifacts for this gate

**Required: the Experiments DB entry** (the DB entry from here on), in the
Growth & Acquisition Experiments DB
(`https://app.notion.com/p/apolloio/1a6ab2b3b496804dad43d766beb7be29`). Read it
as it is; templates change and teams fill them differently.

**For context, in whatever form the team keeps them:** a pre-analysis plan, an
analytics audit or tracking plan, an implementation plan or ERD, the team's
work tracker, and designs. Follow the DB entry's links first. For teams
without a plan format of their own, the Experiment ERD template
(`https://app.notion.com/p/apolloio/Experiment-ERD-Template-1c95d9a3537c4ae5b7728d938bed2833`)
is one layout; items 4 and 5 point at its sections.

**DB entry content this stage depends on.** Before the walk, the DB entry
should have, in some form: the problem and hypothesis, the target audience,
the primary metric, and the experiment design numbers (baseline, effect to
detect, sample, duration). If any of these is empty or still template text,
ask the DRI to fill it before continuing.

**Verdict note.** When the documented runtime is eight weeks or more, or the
DRI says it is not one the team will wait for, add to the verdict line that
the framework treats this as a reason to talk about killing or reshaping the
experiment. The call is the PM's.

## 1. Hypothesis, audience, and primary metric confirmed by all xfn stakeholders

**What this means.** Before anything gets built, you should be able to say in
plain words what you're changing, who will see it, which single metric will
tell you whether it worked, and why you believe the change will move that
metric. The usual shape is IF [change], THEN [metric moves this way], BECAUSE
[reason]; a problem / hypothesis / prediction write-up says the same thing in
more room. The "why" is the part people skip, and it is what turns a flat
result into a lesson instead of a shrug. And the people who need to agree with
that sentence, product, design, data, whoever your team involves, have agreed.

**If no or unsure, ask.**

- Can you read me the hypothesis? Does it name the metric and say why the
  change should move it?
- Who exactly is in the experiment? Is that a rule engineering can build a
  gate from, or a segment name?
- Is the primary metric something the user chooses to do, or a step the
  treatment forces them through?
- Has anyone outside the team pushed back on any of this?

**Complete when:** the hypothesis has all three parts, the audience is stated as
a rule engineering could build from, one primary metric is named the same
everywhere it appears, and the people who need to agree have agreed.

**What can help.** The "Writing a Good Hypothesis" page of the Experimentation
with Amplitude course (`https://apolloio.sana.ai/s/V1sz1uD9tU7m`) for the
hypothesis shape;
`/apollo-eng-experimentation:experiment-pre-analysis-beta` to settle the
primary metric; the PM for the audience rule.

## 2. MDE and runtime estimate documented

**What this means.** An experiment that cannot reach a decision in a time the
team will wait for is not worth starting. So before build you want to know how
long it has to run, and that number should come from real inputs: a fresh
baseline for your primary metric, the smallest change you would still act on,
and how many eligible users actually arrive each week at the point where they
will be exposed. Measured at the wrong point, the volume is wrong and so is
the runtime.

**If no or unsure, ask.**

- Where did the baseline come from, and when was it pulled?
- What is the smallest lift you would still ship for?
- How many eligible users reach the exposure point per week, and was that
  measured at the same point exposure will actually fire?
- Does the runtime follow from those numbers, or was it set first?

**Complete when:** the baseline has a source and a date, the smallest change
worth detecting is stated, weekly eligible volume is measured at the exposure
point, and the runtime follows from those numbers.

**What can help.** `/apollo-eng-experimentation:experiment-pre-analysis-beta`
pulls the baseline and volume fresh and sizes the runtime; the duration guide
the DB entry's template links to, for doing it by hand.

## 3. Initial analytics audit complete, new and existing events and properties spec'd

**What this means.** You cannot learn from what you did not track, and tracking
added after launch cannot be backfilled. So before build you want a written
list of the events this experiment needs: the ones behind your primary,
secondary, and guardrail metrics, which usually already exist; the funnel and
interaction events that will explain *why* it won or lost, some of which
exist; and anything new the treatment lets users do, which does not exist yet.
The list says which exist and which must be built. Building them is Execution's
job; knowing what they are is this step.

**If no or unsure, ask.**

- Is there a written list of the events this experiment needs, or is it in
  someone's head?
- For the events behind your primary and guardrail metrics: do they exist
  today, and does the treatment change anything about when they fire?
- What will you want to know if it loses? Are those events on the list?
- For each new event: does it have a name, a trigger, and properties yet?

**Complete when:** an audit in any form lists the events of all three kinds,
marks each as existing or to be built, gives every new event a name, a trigger,
and its properties, and notes any existing event whose firing might change
under the treatment.

**What can help.** `/apollo-eng-experimentation:experiment-analytics-audit-beta`
produces the audit before build and verifies it after; whoever owns analytics
for the team, if anyone, reviews it.

## 4. Technical approach, risks, and open questions

**What this means.** Before anyone starts building, the team should have a
shared picture of how the change will be built, which parts are essential to
test the hypothesis and which could be cut if time runs short, and what could
still go wrong. Unknowns that would change the plan should have been looked
into, not left to be discovered mid-build, and each risk or open question
should have someone on it.

**If no or unsure, ask.**

- If you had to cut scope tomorrow, do you know what is essential and what is
  not?
- Is there anything about how to build this that nobody has checked yet?
- What is the list of risks and open questions, and does each have someone
  looking at it?

**Complete when:** the approach, risks, and open questions are written down
somewhere you can point to, and each risk and question has an owner or an
answer.

**What can help.** The engineer leading the build usually writes this up;
`/apollo-eng-experimentation:experiment-exposure-design-beta` for eligibility
and exposure-placement questions; the ERD template's Tech Spec and Risks &
Open Questions sections (linked above) as one layout.

## 5. Delivery plan agreed by xfn

**What this means.** The launch date should come from the work, not the other
way round. That means the work is broken down far enough to estimate, the date
follows from those estimates and the people actually available to do it, and
the teams whose surface or code you are touching know the date and have agreed
to it. When most of the code lives in another team's area, that agreement is
the part that matters most, and it often means someone from that team joins
the plan review and stays in the loop through QA.

**If no or unsure, ask.**

- Is the essential work broken down and estimated, including the experiment
  setup and the analytics work?
- Where does the date come from: those estimates, or a target someone set?
- Is the runtime kept separate from the delivery date?
- Have the owners of the surface you are changing heard and agreed to the
  date?

**Complete when:** the essential work is estimated, one launch date follows from
it and reads the same everywhere it appears, the experiment's runtime is kept
separate from the delivery date, and the people you need have agreed.

**What can help.** The engineers doing the work break it down at whatever
planning rhythm the team runs; whoever owns the launch, usually the PM,
confirms the date with xfn and the surface owners and writes it everywhere it
appears; the ERD template's Scope and Milestone Planning sections (linked
above) as one way to get from plan to date.
