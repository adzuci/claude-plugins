# Vendor Pricing — Framework Canonical Reference

> **Status**: framework-canonical. Promoted from `.claude/skills/capacity-planner/references/vendor-pricing.md` in Phase D so that all harnesses, skills, and capacity reviews share one source of truth.
>
> **Effective date**: 2026-Q1. Vendors change pricing without notice.
>
> **Freshness gate**: any harness or skill consuming this file MUST check `last_verified` and warn / block if it is older than 90 days. The `capacity-plan-checker` harness (`pantheon-descriptors/capacity-plan-checker.yaml`) implements this via `block_run_if_vendor_pricing_older_than_90_days`.

---

## Why this is framework-level (not skill-level)

When `vendor-pricing.md` lived only inside `.claude/skills/capacity-planner/references/`, three issues surfaced (Phase B/C reviews):

1. **Cost-attribution harness** needed the same prices to compute USD/run figures and was duplicating the table.
2. **FinOps reports** (Phase D) need vendor pricing for monthly burn projections — they shouldn't import from a skill.
3. **PR-review-bot** wanted to surface "this PR will add ~$X/mo at projected QPS" hints — needed pricing without depending on capacity-planner.

Promoting this file to framework level lets all three consume it without circular dependencies. Skill-local copies become thin pointers to here.

---

## Last verified

```yaml
last_verified: 2026-03-21
verified_by: platform-eng
next_review_due: 2026-06-21
```

> Update both `last_verified` and bump `next_review_due` whenever you refresh prices.

---

## OpenAI

| Model | Input | Output | Notes |
|---|---|---|---|
| gpt-4o | $2.50 / 1M | $10 / 1M | Default for production AI fields |
| gpt-4o-mini | $0.15 / 1M | $0.60 / 1M | Default for cheap classification |
| o3 | check console | check console | Reasoning model — high latency, high cost |
| text-embedding-3-small | $0.02 / 1M | n/a | Default embedding |
| text-embedding-3-large | $0.13 / 1M | n/a | Higher-quality embedding |

> Always model both input and output tokens. A typical AI-field call is ~1500 input + ~200 output tokens, but varies wildly with prompt design.

## Anthropic

| Model | Input | Output |
|---|---|---|
| claude-opus-4 | $15 / 1M | $75 / 1M |
| claude-sonnet-4 | $3 / 1M | $15 / 1M |
| claude-haiku-4 | $0.25 / 1M | $1.25 / 1M |

## Twilio

| Service | Unit | Price |
|---|---|---|
| SMS (US) | per message | ~$0.0079 |
| Voice (US) | per minute | ~$0.014 |
| Phone number lease | per number / month | ~$1.15 |

## SendGrid

| Plan tier | Volume | Per-email cost |
|---|---|---|
| Pro 100k | 100k/mo | ~$0.001 |
| Premier (negotiated) | high volume | check contract |

## AWS S3

| Tier | Storage | GET | PUT |
|---|---|---|---|
| Standard | $0.023 / GB / mo | $0.0004 / 1k | $0.005 / 1k |
| Standard-IA | $0.0125 / GB / mo | $0.001 / 1k | $0.01 / 1k |

## AWS Data Transfer

| Path | Price |
|---|---|
| Out to internet | ~$0.09 / GB |
| Inter-region | ~$0.02 / GB |

## MongoDB Atlas

> Apollo runs Mongo on Atlas. Compute is sized in increments; **adding shards is a multi-week process** — treat as a hard constraint, not a slider.

| Tier | Per-shard / month (rough) |
|---|---|
| M40 | ~$1500 |
| M60 | ~$3000 |
| M80 | ~$6000 |

## Snowflake

| Warehouse | Per-credit | Typical query cost |
|---|---|---|
| XS | $2 (depends on contract) | <1 credit / query |
| S | $4 | 1-2 credits / query |
| M | $8 | 2-5 credits / query |

---

## Pricing-change protocol

When a vendor changes prices:

1. Update this file with new prices and bump `last_verified` + `next_review_due`.
2. Note the previous price as a comment (`# was: $X`).
3. Re-run capacity plans for active features within the past 30 days.
4. Open a PR labeled `framework/vendor-pricing-update`. CI will:
   - Re-run replay-eval for capacity-planner against the new prices
   - Notify FinOps Slack channel
   - Trigger cost-forecast re-projection in `cost-attribution-schema.md` queries

---

## Consumers

Who reads this file (Phase D inventory):

| Consumer | Path | Use |
|---|---|---|
| capacity-planner skill | `.claude/skills/capacity-planner/SKILL.md` | Token / vendor cost projection |
| capacity-plan-checker harness | `pantheon-descriptors/capacity-plan-checker.yaml` | `vendor_pricing_age_days` cost-attribution tag + 90-day freshness gate |
| pr-review-bot harness | `pantheon-descriptors/pr-review-bot.yaml` | Surface "≈$/mo at projected QPS" hints (Phase D) |
| FinOps weekly burn report | `${CLAUDE_PLUGIN_ROOT}/framework/finops/weekly-burn.md` | Vendor-spend projection (Phase D) |
| cost-attribution schema | `cost-attribution-schema.md` | USD/run computation (`analytics.harness_runs.cost_usd`) |

---

## Skill-local pointer pattern

Skills that previously had their own `vendor-pricing.md` should keep a 3-line stub at the original path so deep links don't break:

```markdown
# Vendor Pricing → moved

Promoted to framework. See:
**`${CLAUDE_PLUGIN_ROOT}/framework/references/vendor-pricing.md`**
```

This avoids dual-source drift.
