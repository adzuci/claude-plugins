# Attempt and Repair Contract

Read this reference during stage 1. It defines the bounded-attempt rules: how many repair rounds
the whole attempt gets, what binds across them and gets reused, and when to stop and hand off to
stage 9 instead of continuing.

One invocation is one bounded attempt: one initial pass plus at most two repair rounds within a
60-minute wall-clock deadline. The two-round cap is a single shared counter across
problem-checkpoint, approach-checkpoint, and verification-checkpoint repairs combined — it is not a
separate budget per checkpoint type.

- At intake, record the attempt id, start/deadline, opaque customer reference, and a runtime-provided
  durable evidence location. When established, bind the branch, PR, preview host, and flag target to
  the attempt and reuse those bindings for every repair. Immediately before the approved flag write,
  read and record the authoritative prior value and rollback. The PR head SHA may advance after a
  repair, but record the new SHA and prove that exact revision is deployed. If only ephemeral
  artifact storage is available, stage 6 cannot pass.
- A failed verification records the failed check, observed evidence, proposed change, repair round,
  and checks to reverify. A failed checkpoint records the same fields and draws from the same shared
  repair-round budget. Resume at the earliest affected stage or checkpoint and rerun only it and its
  downstream verification. Do not restart intake or locate, open a second PR, create a new preview,
  recapture an already-valid before state, or repeat an already-applied flag write.
- Do not repeat an already-satisfied approval unless the plan revision, selected approach,
  environment, scope, side effect, or rollback changes. Any such change returns to the relevant
  authorization gate.
- Stages 7 and 8 remain blocked until stage 6 passes. Each repair stays within the approved scope;
  scope expansion returns to the relevant authorization gate.
- On a pass, continue to the next incomplete stage. After two failed repair rounds, unavailable or
  ambiguous verification, lost resource continuity, or deadline exhaustion, go directly to stage 9
  with a partial handoff. Never infer success from missing evidence.
- Runtime session resume is not proof of Loopbot continuity. After interruption, continue only when
  the same branch, PR, preview, rollback, and evidence set can all be re-established; otherwise hand
  off without repeating side effects.
