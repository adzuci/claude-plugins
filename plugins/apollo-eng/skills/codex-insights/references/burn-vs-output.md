# Burn vs Output — session judgment rubric

Read this before writing the burn-vs-output ledger. It mirrors `/apollo-eng:deep-insights`
so the Codex and Claude reports read the same. The lead question is always: **was the spend
worth what it produced?**

Each top-burn session carries three **orthogonal** dimensions. Two are *judged* against
evidence; one is *computed* and must never be overwritten.

## ROI — was the price fair? (judged)

- `worth-it` — the tokens bought durable, useful work at a fair price.
- `overpriced` — real work resulted, but the price was inflated (cold re-ingest, over-reading,
  high reasoning on routine steps). Landed work can still be overpriced.
- `wasted` — little of value resulted, or the result does not hold up.

## Outcome — did durable work result? (judged)

- `landed` — the task completed and the change stuck in the session arc.
- `partial` — some progress, but the work was left unfinished or unverified.
- `dropped` — the thread ended without durable output, or the work was abandoned.

## Efficiency — how much spend was avoidable churn? (computed, not judged)

`lean` / `loose` / `thrashy` is emitted deterministically by the enumerator from cold-reingest,
large-tool-output, tool-loop, and reasoning-spin signals. **Do not opine on it or change it.**
It is free and reproducible; the enumerator merges it onto the ledger. Spend your judgment on
ROI and outcome, where it adds value.

## Grounding rules

- **Judge from evidence, not vibes.** Use the deterministic per-session signals the enumerator
  provides (tokens, credits, `edit_events`, `test_events`, `commit_events`, `user_prompt_count`,
  `completed`, flags, efficiency signals). If you need verbatim confirmation, read only the
  targeted lines you need from the session file (`sed -n`/`jq`) — never `cat` a whole transcript.
- **Commit/edit counts are noisy outcome signals.** Work is often committed in another session,
  by hand, or squashed later; zero commits does **not** mean nothing landed. Read "landed" from
  whether the work completed and stuck, not from a raw count.
- **Efficiency and ROI/outcome can disagree.** A session can be `landed` + `overpriced` + `loose`
  (useful, but pricier than it needed to be). Keep the three independent.
- **Materiality first.** Do not write a verdict for trivial token amounts, expected setup
  overhead, or low-stakes micro-habits. A clean, small session needs no ledger row.
- **One blunt line per session.** Each verdict is a single sentence a busy engineer can act on.
- **Overall verdict is week-aware.** Close with "of ≈$X credits, roughly how much bought work
  that landed and was worth the price vs exploration / churn / abandoned effort," and read the
  trend across weeks from `by_week`.

## Output shape (judgments.json)

```json
{
  "overall_verdict": "one week-aware sentence",
  "weekly": [{ "week": "YYYY-MM-DD", "headline": "one line for that week" }],
  "sessions": [
    { "id": "<session id from burn_analysis.sessions[].id>",
      "roi": "worth-it|overpriced|wasted",
      "outcome": "landed|partial|dropped",
      "verdict": "one blunt actionable sentence" }
  ]
}
```

Only include a session `id` that already exists in the enumerator's `burn_analysis.sessions`.
Leave `efficiency` alone — the renderer merges the computed label automatically.
