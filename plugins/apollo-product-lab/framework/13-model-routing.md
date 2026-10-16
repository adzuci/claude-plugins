# 13 — Model routing and cross-family verification

> Companion to [12-product-harness.md](./12-product-harness.md). Governs which model runs which role, and why.
> **Status: draft for review. Nothing binding.**

## 1. The two things model choice buys, and they are different

Conflating these produces bad architecture in both directions.

| Goal | What it needs | Whether family diversity helps |
|---|---|---|
| **Capability** — better output on a task | The strongest model that fits the budget | Maybe. Empirical, per task |
| **Decorrelation** — independent verification | Voters whose errors are *not* correlated | **Yes, and nothing else substitutes** |

A better model raises per-item accuracy and does **nothing** to correlation. Model quality and voter independence are orthogonal axes. This is the single most common mistake in multi-agent review design, and it is easiest to make when the model is excellent — the panel will be articulate, unanimous, and wrong together.

## 2. Family taxonomy

Decorrelation requires crossing a **lineage** boundary, not a version boundary.

| Family | Members | Decorrelation value as a co-voter |
|---|---|---|
| Claude | Opus 4.8, Sonnet 5, **Fable 5**, Haiku 4.5 | **Low.** Shared architecture and pretraining lineage. Different training runs give partial decorrelation at best |
| Other vendors | GPT-family, Gemini-family, others | **High.** Independent training data, architecture, and RLHF |

**Fable 5 is a Claude model** (`claude-fable-5`). Pairing it with Opus does not satisfy the cross-family rule; it is a same-lineage pair. Recorded explicitly because the model names do not make the lineage obvious, and the mistake is invisible until a quorum agrees confidently on something wrong.

**Harness ≠ model.** Codex is an agent loop and IDE that happens to run a non-Claude model. For quorum purposes what matters is the *model* being callable as a reviewer. A competing coding tool is not a voter — it is a peer product, and in this case one that is deliberately human-triggered (`disable-model-invocation: true`). Do not count it as cross-family coverage while it cannot be dispatched.

## 3. Current reality: Apollo has five model families in production

An earlier draft of this section claimed "no cross-family path exists." **That was wrong, and the error is worth recording.** It was true of one Claude Code session's tool surface (no LLM-provider MCP, no provider CLI, no keys) and was then generalised to Apollo. Two different claims. Verified 2026-09-03:

| Provider | Status | Production models | Notes |
|---|---|---|---|
| **OpenAI** | Production, broadest use | `gpt-4o-mini`, `gpt-5-nano`, `gpt-5.1`, `o3`, `o3-mini`, `gpt-5.4` (i18n CI) | Per-cost-centre keys: `OPENAI_API_KEY`, `MI_`, `ND_` |
| **Google Gemini via Vertex** | Production, feature-gated | `gemini-3.1-flash-lite` | `magic_field_generation_service.rb:747`, flag `magic_column_v2` |
| **Perplexity** | Production | `sonar-pro` | Via GenAi templates and DAPI |
| **Groq** | Production, narrow | `llama-3.3-70b-versatile` | i18n CI fallback |
| **Self-hosted open weights** | Production | Mistral 7B, Llama 3.1 8B | Ray Serve + vLLM |
| Anthropic | Production | `claude-haiku-4-5-20251001`, `claude-sonnet-4-6` | `PLAYS_ANTHROPIC_API_KEY` |

Zero presence: Azure OpenAI, Bedrock, Cohere, HuggingFace hosted, Ollama.

**The Gemini contradiction, resolved.** Two research passes disagreed on whether Gemini is in production. It is — on `origin/master`, with the flag literally named *"Magic Column V2 (Gemini + v7 prompt)"* in `config/feature_flags/agent-core-be.yml:67`, unexpired until 2026-12-31. The apparent conflict was a **team-scoped** deprioritization: Agent Core dropped Gemini for the AI Assistant in Dec 2025 (AIASSIST-529, "infra limitations"), while AI Capabilities independently shipped it for Magic Column on cost grounds seven months later. Both accounts were true of their own scope.

Two honest limits. Whether `magic_column_v2` is actually *enabled* in production is unknown — rollout percentage lives in the `FeatureFlag` collection, not the repo. And `gemini-1.5-flash` is **not** production; it appears only in a spec fixture.

**Governance inference** (flagged as inference, no document found stating it): Gemini reaches production via Vertex AI, which is Google Cloud — an already-contracted platform. That plausibly explains why it needed no new vendor relationship, in contrast to Baseten which required a fresh MSA and DPA.

### Reachability is solved — twice, in production

**1. `dapi/lib/llm` is a real multi-provider router.** `providers/enums.py` defines a `Provider` enum with **ten** providers: `openai`, `azure_openai`, `perplexity`, `groq`, `fireworks`, `anthropic`, `gcp_anthropic`, `vertexai`, `vertexai_v2`, `baseten`. `provider_cls()` maps each to a client; **`failover_provider()` already does automatic cross-vendor failover** (OpenAI↔Azure, Anthropic↔GCP-Anthropic). `config.py`'s `LLM_CLIENT_CONFIGS` is a per-use-case map of 21 `LLMClientID`s, each with its own GCP secret (`dapi-agent-smith-openai-api-key`, `dapi-magic-column-openai-key`, …). A second HTTP-proxy layer lives in `dapi/lib/llm/gateway/`.

**2. Pantheon's agent-descriptor schema already carries the fields.** `config/schemas/agent-descriptor.schema.json:180` has `provider` (enum `["claude","codex"]`, default `claude`) and a sibling `model` string. `docs/provider-and-model-selection.md` specifies a **four-tier resolution**: `X-Pantheon-Provider`/`X-Pantheon-Model` headers → trigger payload → descriptor → platform default. Defaults are `claude: claude-opus-5[1m]` and `codex: gpt-5.6-sol`. The resolved pair persists to `runs.provider` / `runs.model`, and both are selectable in the run-trigger UI. Codex support merged as PR #237 on 2026-08-15.

**3. Auth needs no new secrets.** There are no raw provider keys in Pantheon. `internal/runtime/argo/wft.go` points both `ANTHROPIC_BASE_URL` and `PANTHEON_ACP_CODEX_BASE_URL` at the same gateway and injects one **provider-neutral** token (`dapi-llm-gateway-auth-token`) as both `ANTHROPIC_AUTH_TOKEN` and `CODEX_API_KEY`. So Pantheon's Codex path terminates in dapi's gateway, and `gpt-5.6-sol` is a live Azure OpenAI deployment.

**And Apollo's flagship assistant supervisor is already non-Anthropic.** `assistant_config.py:39` — `SUPERVISOR_MODEL = AiModelIdentifiers.GPT_4_1`, hardcoded, used by `supervisor.py` and `router.py`. Sub-agents run Claude via `Provider.GCP_ANTHROPIC`. A cross-vendor supervisor/worker split is not a proposal here; it is what production does.

#### Cheapest path for a cross-family reviewer

Register the reviewer as a **Pantheon descriptor** and pass `X-Pantheon-Provider: codex` plus `X-Pantheon-Model: <id>` per run. Zero new secrets, and the resolved pair is already recorded per run for audit.

Two real constraints:

- The provider enum is **closed** at `{claude, codex}`. Anything else needs a Go change in Pantheon.
- Codex is dispatched as a **CLI harness** (config.toml, `--strict-config`), not a raw API call. A reviewer that wants plain completions is better served calling the dapi gateway directly with a new `LLMClientID` and its own `dapi-*-api-key` secret.

One eval gotcha worth encoding now: `runs.model` records what was **requested**, not what was served. For any model comparison (§6), read the `model` attribute on the `run.started` event instead.

#### Two control points that are not control points

`SUPPORTED_PROVIDERS = %w[perplexity anthropic openai]` (`ai_prompt_template.rb:132`) is **not** comprehensive — Magic Column reaches Gemini via `provider: "vertexai_v2"`, bypassing it entirely. And there are **two** shared client layers (`lib.llm` in data-platform, DAPI in leadgenie), so the AI Org doc's claim that AI Infra owns "one choke point for all model calls" is not currently true. Do not design a gate on either assumption.

**The rule against adding Claude voters still stands.** Three Claude models voting is a 3x bill for correlated agreement, regardless of how easy dispatch becomes.

#### A framework decision resting on a false premise

D1 in [01-decisions.md](./01-decisions.md) dismisses dapi as *"Python-only, embedded in the AI Assistant pack… it's not infrastructure. Promote the pattern, not the runtime."*

That is now demonstrably wrong. `dapi-llm-gateway.prod.apollo-dapi.app` is a network service that **Pantheon itself depends on for all LLM traffic, including Claude**. dapi is not an embedded library that happens to orchestrate; it is the model-access infrastructure layer beneath the runtime D1 designates as canonical. D1's conclusion (Pantheon as sole agent runtime) may still be right, but its stated reasoning about dapi is false and should be corrected before anyone cites it.

## 4. Data handling — the actual gate, and it is stricter than expected

The **Apollo Organizational AI Policy** v1.0 (Aug 2025) requires the cross-functional **AI Governance Committee** (Security, Legal, Engineering, Product, Ops) to approve **in advance**: launching any new AI feature or model; engaging a new AI vendor **or adding a new use case for an existing vendor**; and using customer data for training.

**That last clause is the one that binds Stage E.** Using OpenAI as a quorum voter is a *new use case for an existing vendor*, so "OpenAI is already approved" does not carry. The vendor relationship is free; the use case is not.

Binding constraints, from the policy and two companion standards:

| Constraint | Source | Effect on the harness |
|---|---|---|
| Never send Confidential or Critical data to public AI tools. No confidential business info, PII, customer data or credentials into generative AI without Legal + Security approval. Prompts must be sanitised. | AI Policy | **An unreleased PRD and a legal constraint register are confidential business info.** Stage E over those artifacts is the hard case |
| **#35 — "Egress of code or metadata to model providers MUST stay within approved regions"** | Automated & AI-Assisted Change Approval Standard (Jul 2026) | Sending diffs to a cross-family reviewer is explicitly governed, not incidental |
| **#34 — any third-party model/service MUST operate under approved enterprise terms** (no training on Apollo data, short retention) | same | Rules out ad-hoc keys and personal accounts |
| **No-Go list: a bot may not solo-approve changes in those areas; independent human approval required** | same | Independently validates the human-gate design in the harness doc |
| Third-party LLMs contractually may not train on Apollo or customer data; **deletion within 30 days** | Data Usage Legal Guidelines | Constrains which providers qualify at all |
| **Customer data must not be used to test new vendors** — it would make them a sub-processor and trigger DPA notification. Use dummy data. | same | Any Stage E eval must run on synthetic or internal-only artifacts |

**The canonical approved-vendor list could not be retrieved.** The policy links to it; the target is not reachable via Glean or Notion. Corroborating that no queryable source of truth exists: `claude-plugins` PR #179 (unmerged) adds a `/apollo-eng:tool-intake` skill for exactly this lookup and ships its approval snapshot marked `UNCONFIGURED`.

**Spend governance, for reference.** `ai-overage-admins` covers exactly two vendors, Anthropic and OpenAI. Combined Claude + Codex under **$1,050/mo** per engineer auto-approves; $1,051–2,000 requires a Director tag; **above $2,000 goes to Himanshu Gahlot**, the named budget owner. Note this is *spend* governance and says nothing about content approval — the distinction this section exists to make.

### An infosec finding the harness would amplify

The open-weight evaluation document admits gateway-level input/output filtering **does not exist**: *"Today's Claude and OpenAI traffic runs without it."* LangChain's `PIIMiddleware` is available and unused. There is no prompt-injection check and no output-policy check anywhere in the path.

A harness that routes PRDs, legal registers and source diffs through model providers would materially increase the volume and sensitivity of traffic crossing that unfiltered boundary. Worth raising with Security **independently of whether Stage E ships**, because it is a pre-existing gap that this work makes more consequential rather than one this work creates.

## 5. Per-role routing

Status column is the point of this table. **`assumed` is a hypothesis, not a decision**, and the framework's own sourcing rule applies to claims about models exactly as it does to claims about platforms: an unsourced claim is deleted, not hedged.

| Role | Assignment | Status | Rationale |
|---|---|---|---|
| Stage A deterministic phases (1–3, 5) | Haiku | **assigned** | Mechanical: schema checks, date comparisons, coverage mapping. Cheapest tier that can do it |
| Stage A Phase 4 (contradiction detection) | Opus | **assigned** | Judgment over two documents; the quality-sensitive part of an otherwise cheap stage |
| Stage B codebase-reality | Opus | **assigned** | Long multi-file reasoning with citation discipline |
| Stage B external acquisition | Haiku or Sonnet | **assigned** | Retrieval and tiering, not judgment |
| Function-team specialists (C, D) | Opus | **assigned** | Analysis producing new conclusions |
| Function-team arbiters | Opus | **assigned** | Synthesis under explicit dissent rules |
| **Stage E quorum voters** | **≥1 non-Claude required** | **unblocked technically, gated on approval** | Dispatch path exists (§3). Remaining gate is an AI Governance Committee use-case approval plus the content-class question (§4) |
| **Stage E mandated adversary** | Non-Claude preferred | same | A refuter sharing the proposer's lineage shares its blind spots |
| Compliance constraint extraction | Opus | **assigned** | Prose-to-assertion conversion; precision matters more than breadth |
| Compliance judgment | **none — human** | **assigned** | Hard boundary. No agent issues a legal verdict |
| Slice owners (Stage F) | Opus | **assigned** | Inherits `auto-pr` |
| Integrator (Stage F) | Opus | **assigned** | Cross-slice semantic reasoning |

**Every `assigned` row above is a cost/capability judgment, not a measured result.** None has been A/B'd. That is acceptable for cost tiering, where being wrong is cheap and visible. It is not acceptable for a claim that one model is better at a *domain*.

## 6. Turning capability claims into measurements

Claims of the form "model X is better at Y" are testable, and the harness already has the machinery. Protocol:

1. **Pick the role, not the domain.** "Better at legal" is unmeasurable. "Higher recall on constraint-register invariant extraction, at equal or lower false-positive rate" is measurable.
2. **Use the existing eval shape** — `.claude/skills/tdd-loop/eval/cases.json`: per-case `expected`, `anti_expected`, weights, and a gate with `precision_min` / `fpr_max` / `support_min`. The `anti_expected` field is what catches over-reporting, which is the dominant failure mode for every review-shaped role here.
3. **Hold the prompt constant, vary only the model.** Otherwise you have measured prompt engineering.
4. **Score against human adjudication**, not against another model. An LLM-judged model comparison inherits the judge's correlated bias, which is the problem being investigated.
5. **Report the delta with support size.** A 2-point difference over 5 cases is noise.
6. **Promote the winner into §5 and change its status to `measured`**, with the case count and date.

The first candidate is the one currently asserted: **does a different Claude model outperform Opus at invariant extraction from a constraint register?** The reference instance produced 9 invariants from ~30 register items, hand-checked. That is a small but real starting corpus, and it is the same corpus Q1 needs.

Note the honest constraint: this protocol measures *capability*, and capability is not decorrelation. Winning the eval does not make a model a valid co-voter with its own family (§2).

## 7. Portability: running the harness on another agent tool

The strategic question is separate from routing, and worth naming because the answer is not obvious.

**What ports cheaply.** `claude-plugins` already ships dual `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, so Apollo already does dual-target distribution. Skills are markdown with frontmatter. Knowledge files are plain markdown. Document-graph configs are YAML. The document-graph, the taxonomies, the tiering rules, and the decomposition rule are all tool-agnostic by construction.

**What may not port, and it is the load-bearing part.** The enforcement layer is hooks: `PreToolUse` fires before the permission check, `exit 2` overrides any model-issued allow, and hooks fire even under permissive modes at zero context cost. **If the target tool has no equivalent with deny semantics, every gate degrades to a prompt** — and a prompt-level gate is the thing the harness explicitly rejects, because it asks the model to decide both the action and whether to ask first.

So portability hinges on one question: **does the target harness support a deterministic, model-overridable-by-nobody pre-execution deny hook?** If yes, port it. If no, the harness can be *distributed* to that tool but its gates are advisory there, and that has to be stated rather than discovered.

Secondary unknowns: sub-agent dispatch with isolated context, worktree isolation for parallel writes, and whether skill progressive-disclosure has an equivalent. All are optimisations; the hook question is the gate.

## 8. Open questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| M1 | ~~Which cross-family option is approved?~~ **Answered (§3): dispatch exists via Pantheon `provider: codex`, or directly against the dapi gateway with a new `LLMClientID`.** Remaining sub-question: Pantheon's provider enum is closed at `{claude, codex}` — is a Go change wanted, or is the dapi-direct route preferred? | AI Tooling | Implementation shape only |
| **M2** | **The actual blocker.** AI Policy requires advance AI Governance Committee approval for *"adding a new use case for an existing vendor."* A Stage E quorum voter is a new use case. Also unresolved: whether an unreleased PRD and a legal constraint register count as Confidential business info, which would require Legal + Security approval before any egress. | Security + Legal | **Stage E entirely** |
| M3 | Is the "better at legal/compliance" claim real? Run §6's protocol before encoding it. Note the eval gotcha: read `model` from `run.started`, not `runs.model` | author | Only the routing table |
| M4 | ~~Does the target tool have a deny-semantics hook?~~ Partly answered: Pantheon already dispatches Codex as a first-class provider, and every `claude-plugins` plugin ships dual manifests. **Still open: does Codex-as-harness expose a pre-execution deny hook**, or do gates degrade to prompts there (§7)? | AI Tooling | Any port decision |
| M5 | ~~If no cross-family path is approved, does Stage E ship without quorum?~~ **Reframed: the path exists, so this is now purely an approval-sequencing question.** Ship Stage E with deterministic gates first and add the cross-family voter when M2 clears, or hold Stage E until M2 clears? Recommendation: ship deterministic-first — the gates carry most of the value and do not wait on a committee | Eng leadership | Stage E sequencing |
| M6 | Correct D1's stated reasoning about dapi (§3), which is factually wrong now. Its conclusion may stand; its premise does not | Framework custodian | Framework accuracy |
| M7 | Raise the unfiltered-egress gap with Security independently of this harness: no gateway input/output filtering, no PII middleware, no prompt-injection or output-policy check on any Claude or OpenAI traffic today (§4) | Security | Nothing here, but it is the largest standing risk found |
