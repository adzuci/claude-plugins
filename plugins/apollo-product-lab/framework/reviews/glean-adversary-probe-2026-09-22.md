# Probe: can the Glean family play the adversary lens? (2026-09-22)

**Question (Akansh):** why not run the adversary on Gemini or DeepSeek through Glean, instead of only OpenAI via shunt?

**Method.** One `glean_default.chat` call from Claude Code with an adversary brief and the Ads data-model
decision ("provider-neutral AdConnection from M1"), asking it to (1) name its model, (2) name its input
cap, (3) say whether it can read `apolloio/leadgenie` and cite a `packs/ads/` file, (4) object in a table.

**Result.**
- Model and vendor: **unknown** (it could not state them). Glean docs: the Assistant engine "runs on GPT-5 or
  Claude Sonnet models that are supported by your deployment"; Gemini 3.1 Pro is also selectable; the admin
  chooses in the Model Hub. No Apollo-internal record of that choice was found in Glean or Slack.
- Input cap: unknown.
- Repository: **yes, through Glean's GitHub index**, at `master` only. It saw
  `shared/configs/third_party_integrations/tray/google_ads.yml` but nothing under `packs/ads/`, which lives
  on an unmerged branch. So: index reads of merged code, not file reads at the reviewed sha.
- Review quality: six objections with evidence-needed columns (lowest-common-denominator abstraction, roadmap
  intent vs commitment, M1 surface, provider field vs capabilities, unstable central assumptions, complexity
  budget). Comparable to the Astra adversary's first pass on the same decision; no repo-grounded objection.

**Decision.** Glean is an **adversary route**, ranked after OpenAI via shunt and the Codex plugin and before
a same-family Anthropic fallback:
- prd and design kinds: full route (document artifacts fit one message; chunk above ~6k words).
- erd, plan, pr kinds: tagged `excerpt-only` and `repo: glean-index@master`; a branch-only change gets no
  repo grounding from it.
- Independence: `unknown` until `glean.assistant_model` in the registry is filled from the Model Hub by AI
  Tooling. If it turns out to be Claude Sonnet, the Glean adversary is same-family with an Anthropic author
  and earns no independence credit; if GPT-5 or Gemini, it does. `independence: unknown` is never treated as
  independent (doc 34 §3), so today it improves the review without changing the gate.
- DeepSeek: not in Glean's Model Hub list and has no other lane; still unavailable.
- Data handling: Glean is an approved vendor and already indexes the artifacts, so sending them back is inside
  the existing approval (doc 13 §4).

**Owner action.** Ask AI Tooling which model the Glean Assistant is set to in Model Hub; write it to
`models/model-registry.yml` under `glean.assistant_model` with the date.

---

## Head-to-head on the same artifact (2026-09-22, second probe)

**Setup.** The recorded Astra adversary review of the Ads data-model decision
(`.ai/ads-builder/runs/ads-m1-run1/council.adr-p3.adversary.md`, gpt-6-astra xhigh through shunt, with
repo tools, 3,900 words) is the baseline. Glean got the same decision, the same design and invariant
excerpts, and the same six model files plus the launcher, as text in one chat message, with the same
five questions and the same output contract. Because Glean cannot read the branch, the operator had to
condense the code to about 8k words, which is itself a bias: the reviewer only sees what the operator
chose to show.

**Result, defect by defect** (Astra's code-grounded findings, and whether Glean found them):

| Astra finding | Glean |
|---|---|
| F2 `contribution_ids` (a query) and the payload (`evaluation.eligible`) are selected independently | noted the two selections as a scale issue; did not derive the payload mismatch |
| F3 `mark_submitted!` overwrites `removal_pending` unconditionally; late acknowledgement erases a withdrawal | noted "unconditionally changes rows to submitted" as a fact; did not derive the lost-removal race |
| F4 exclusion upsert sets `expires_at` on previously submitted rows, so the TTL guard is contradicted | **missed**, although the brief pointed at the line |
| F6 provider audience created before any durable record; crash window leaves an orphan audience | noted the order as a fact; did not derive the orphan |
| F7 `run_at` cannot prove chunk completeness | found ("no durable run cursor, chunk identity") |
| D4 destination generations on re-provisioning | found |
| D6 single `request_id` cannot hold several attempts | found |
| D9 "one enum value, one transport" is an assertion, not a provider contract | found |
| D10 the "one active sync per source" index is neither unique nor partial on active | found, including the partial-on-active point |
| D11 the "~1 day of renames" estimate must be withdrawn | **missed** |
| Glean-only objections | "migration semantics from `customer_id`" (wrong: the decision says no data exists); "C5 fails because rows are written `submitted`" (misreads C5: `submitted` is the C5-compliant word, `matched` is the forbidden one) |

Score: of ten code-grounded Astra defects, Glean found five, half-derived three (right fact, no failure
trace), missed two, and added two objections that do not hold. No hallucinated code or paths. It could not
name its model. Turnaround about one minute at flat license cost.

**Read against the competitor article** (getunblocked.com, "Is Glean good enough", a vendor piece): its
documented claims hold in this test, GitHub indexed as text chunks at `master`, per-user OAuth, no code
graph; its conclusion that Glean "cannot explain code" is too strong, the reviewer reasoned correctly from
the code it was shown. The gap is derivation depth and repo reach, not comprehension.

**Glean CLI / coding-host plugin.** `/plugin marketplace add gleanwork/claude-plugins` then
`/plugin install glean@glean-plugins` adds task-triggered Glean skills on top of the same MCP connection.
It exposes no model choice and no served-model field, so it changes nothing for the adversary question.

**Revised decision.**
1. **prd and design kinds:** Glean stays an adversary route after OpenAI via shunt and the Codex plugin,
   ahead of a same-family Anthropic fallback. Document artifacts fit one message and the first probe
   showed competent objections. Tag `independence: unknown` until `glean.assistant_model` is confirmed.
2. **erd, plan and pr kinds:** Glean is **not** an adversary fallback. Half the value of the Astra review
   was tracing a failure through code it read itself; Glean depends on the operator's excerpt and
   under-derives consequences. When shunt and Codex are unavailable the code-kind adversary is the
   same-family Anthropic fallback, tagged, and Glean may run as an optional **second reading** appended
   to the memo, labelled as such and never counted as the adversary lens.
3. **Model Hub confirmation** stays the one action that can promote Glean; it does not change point 2.
4. **DeepSeek:** still no lane.
