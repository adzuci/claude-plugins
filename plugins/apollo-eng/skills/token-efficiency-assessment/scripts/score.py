#!/usr/bin/env python3
"""
score.py — Combines env-report + conversational answers into a final score.

Env report comes from check_env.py.
Answers come from the skill's AskUserQuestion collection.

Answers JSON schema (15 keys; root_cause is informational only):

  {
    "root_cause":             ["long_conversations", ...],   // not scored
    "uses_compact":           "yes"(1) | "sometimes"(0.5) | "no"(0),
    "context_window_pct":     "under_50"(1) | "50_to_80"(0.5) | "over_80"(0) | "unsure"(0),
    "checks_ccflare":         "yes"(1) | "no"(0) | "unsure"(0),          # binary
    "fresh_conversations":    "yes"(1) | "sometimes"(0.5) | "no"(0),
    "log_sharing":            "files"(1) | "mix"(0.5) | "inline"(0),
    "image_pasting":          "never"(1) | "sometimes"(0.5) | "often"(0),
    "prompt_language":        "english"(1) | "mixed"(0.5) | "non_english"(0),
    "model_switching":        "yes"(1) | "sometimes"(0.5) | "no"(0),
    "opus_only":              "yes"(1) | "sometimes"(0.5) | "no"(0),
    "opusplan_known":         "yes_use"(1) | "yes_know"(0.5) | "no"(0),
    "prompt_quality":         "specific"(1) | "mixed"(0.5) | "vague"(0),
    "uses_plan_mode":         "yes"(1) | "sometimes"(0.5) | "no"(0),
    "batching":               "yes"(1) | "sometimes"(0.5) | "no"(0),
    "subagent_overuse":       "no"(1) | "sometimes"(0.5) | "yes"(0),
    "mcp_payloads_reasonable":"yes"(1) | "sometimes"(0.5) | "no"(0)
  }

Usage:
    python3 score.py --env env-report.json --answers answers.json
    python3 score.py --env env-report.json --answers-json '{"uses_compact": "yes", ...}'
"""

import argparse
import json
import sys

# Human-readable label for each conversational answer key
ANSWER_LABELS = {
    "uses_compact":               "Uses /compact or /clear proactively",
    "context_window_pct":         "Context window under 50%",
    "checks_ccflare":             "Checks ccflare dashboard",
    "fresh_conversations":        "Starts fresh conversations per task",
    "log_sharing":                "Points Claude to files on disk (not pasted inline)",
    "image_pasting":              "Does not paste images into chat",
    "prompt_language":            "Writes prompts in English",
    "model_switching":            "Switches to Haiku/Sonnet for simple tasks",
    "opus_only":                  "Uses Opus only for deep-reasoning tasks",
    "opusplan_known":             "Knows and uses opusplan mode",
    "prompt_quality":             "Writes clear, specific prompts",
    "uses_plan_mode":             "Uses /plan before large tasks",
    "batching":                   "Batches related changes in one conversation",
    "subagent_overuse":           "Does not overuse subagents (uses Grep/Glob instead)",
    "mcp_payloads_reasonable":    "MCP tool call payloads are a reasonable size",
}

# Scoring lookup: answer value → score
# Scale: 1 = full credit, 0.5 = partial (sometimes/mix), 0 = no credit
# Env signals (in check_env.py) are binary 0/1 — only conversational answers use 0.5.
# Binary questions (no meaningful partial state) stay on 0/1.
ANSWER_SCORE_MAP = {
    #                              yes      partial    no
    "uses_compact":               {"yes": 1, "sometimes": 0.5, "no": 0},
    "context_window_pct":         {"under_50": 1, "50_to_80": 0.5, "over_80": 0, "unsure": 0},
    "checks_ccflare":             {"yes": 1, "no": 0, "unsure": 0},          # binary
    "fresh_conversations":        {"yes": 1, "sometimes": 0.5, "no": 0},
    "log_sharing":                {"files": 1, "mix": 0.5, "inline": 0},
    "image_pasting":              {"never": 1, "sometimes": 0.5, "often": 0},
    "prompt_language":            {"english": 1, "mixed": 0.5, "non_english": 0},
    "model_switching":            {"yes": 1, "sometimes": 0.5, "no": 0},
    "opus_only":                  {"yes": 1, "sometimes": 0.5, "no": 0},
    "opusplan_known":             {"yes_use": 1, "yes_know": 0.5, "no": 0},  # use > know > unaware
    "prompt_quality":             {"specific": 1, "mixed": 0.5, "vague": 0},
    "uses_plan_mode":             {"yes": 1, "sometimes": 0.5, "no": 0},
    "batching":                   {"yes": 1, "sometimes": 0.5, "no": 0},
    "subagent_overuse":           {"no": 1, "sometimes": 0.5, "yes": 0},
    "mcp_payloads_reasonable":    {"yes": 1, "sometimes": 0.5, "no": 0},
}

ENV_SIGNAL_LABELS = {
    "claudeignore_configured":    "Has .claudeignore configured",
    "claude_md_lean":             "Keeps CLAUDE.md lean (≤200 lines)",
    "mcp_count_reasonable":       "Only necessary MCPs/plugins enabled",
    "budget_guardrail_set":       "Has --max-turns or token budget configured",
    "permission_mode_non_auto":   "Uses non-auto-accept permission mode",
    "tool_search_tuned":          "Tool Search threshold tuned below default",
    "memory_populated":           "Caches repeated context in memory",
}


def _verdict(score):
    # Thresholds hold for both integer and float totals (max 22).
    # With 0.5 partial credit, a score of e.g. 17.5 correctly lands in "Needs improvement".
    if score >= 18:
        return "Yes"
    elif score >= 12:
        return "Needs improvement"
    return "No"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", metavar="FILE")
    parser.add_argument("--env-json", metavar="JSON")
    parser.add_argument("--answers", metavar="FILE")
    parser.add_argument("--answers-json", metavar="JSON")
    args = parser.parse_args()

    if args.env:
        env_data = json.loads(open(args.env).read())
    elif args.env_json:
        env_data = json.loads(args.env_json)
    else:
        print("ERROR: supply --env FILE or --env-json JSON", file=sys.stderr)
        sys.exit(1)

    if args.answers:
        answers = json.loads(open(args.answers).read())
    elif args.answers_json:
        answers = json.loads(args.answers_json)
    else:
        print("ERROR: supply --answers FILE or --answers-json JSON", file=sys.stderr)
        sys.exit(1)

    env_signals = env_data.get("signals", {})

    # Score env signals
    env_scored = {}
    for key, label in ENV_SIGNAL_LABELS.items():
        sig = env_signals.get(key, {})
        env_scored[key] = {
            "label": label,
            "score": sig.get("score", 0),
            "value": sig.get("value"),
            "fix": sig.get("fix", ""),
        }

    # Score conversational answers
    answer_scored = {}
    for key, label in ANSWER_LABELS.items():
        raw = answers.get(key, "")
        score = ANSWER_SCORE_MAP.get(key, {}).get(raw, 0)
        answer_scored[key] = {"label": label, "score": score, "value": raw}

    total = sum(s["score"] for s in env_scored.values()) + sum(
        s["score"] for s in answer_scored.values()
    )
    max_score = len(env_scored) + len(answer_scored)  # 22

    strengths = [s["label"] for s in env_scored.values() if s["score"] == 1] + [
        s["label"] for s in answer_scored.values() if s["score"] == 1
    ]

    red_flags = [
        {"label": s["label"], "fix": s.get("fix", "")}
        for s in env_scored.values()
        if s["score"] == 0
    ] + [
        {"label": s["label"], "fix": ""}
        for s in answer_scored.values()
        if s["score"] == 0
    ]

    result = {
        "score": total,
        "score_max": max_score,
        "verdict": _verdict(total),
        "strengths": strengths,
        "red_flags": red_flags,
        "root_cause": answers.get("root_cause", []),
        "env_signals": env_scored,
        "answer_signals": answer_scored,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
