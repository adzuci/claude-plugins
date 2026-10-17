# Ensemble Mode (`--ensemble`)

An optional independent-verification pass over the same evidence before finalizing a block recommendation, using [Codex](https://github.com/openai/codex-plugin-cc) ("Sol") alongside Claude — the same cross-model fact-check pattern used for other fraud/incident conclusions at Apollo: don't present a single model's read of production evidence as confirmed without an independent check.

## Preflight: Check for Codex

Before attempting an ensemble pass, verify Codex is actually usable — do not assume the plugin being installed means the CLI works.

1. Check the Claude Code plugin: `claude plugin list` — look for `codex@openai-codex` enabled. If absent, do not install it yourself: report "Codex plugin missing" and continue without the ensemble pass. Tell the human the setup path (the `openai-codex` marketplace and `codex@openai-codex` plugin) so they can install it from an approved source if they want.
1. Check the underlying CLI actually resolves and runs: `which codex` and `codex --version`. A wrapper function resolving to a path that then errors "no such file or directory" means the plugin is installed but the CLI binary itself is missing or broken — this is a real, distinct failure mode from "plugin not installed," and has been observed in practice. Do not reinstall it yourself; report which of the two states (plugin missing vs. CLI broken) was found and let the human run `/codex:setup`.
1. If authentication/config hasn't been done, report it; the human runs `/codex:setup`. Never enter or request credentials.
1. If any step fails, report the exact failure and continue the skill's normal (non-ensemble) workflow rather than blocking the whole investigation on Codex being available — ensemble mode is additive verification, not a hard dependency.

## Running the Pass

Once Codex is confirmed working, resolve the currently available review/rescue command at invocation time, then hand it the same underlying evidence (IOC matches, ring membership, complexity inputs, past-ring Glean results) — not just Claude's conclusion. Ask it to independently assess: is this really a ring match, is the complexity score reasonable, is the monitor-vs-block recommendation right. The ensemble pass counts against the same `--max-turns` and `--time-budget` caps as the primary investigation; if the remaining budget is insufficient, skip it and report that explicitly. Present agreement or disagreement explicitly in the report; do not merge the two into a single unattributed answer. On disagreement, surface both readings to the human reviewer rather than picking one.

## Degradation

If Codex cannot be made to work (CLI broken, no auth available, marketplace unreachable), state that clearly and proceed without the ensemble pass. Never fabricate a "Codex agrees" result.
