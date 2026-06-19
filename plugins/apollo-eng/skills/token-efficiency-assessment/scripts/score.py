#!/usr/bin/env python3
"""
score.py — Combines env-report + context-report + conversational answers into a final score.

Env report comes from check_env.py.
Context report comes from analyze_context.py.
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
    python3 score.py --env env-report.json --context context-report.json --answers answers.json
    python3 score.py --env env-report.json --answers-json '{"uses_compact": "yes", ...}'
"""

import argparse
import json
import sys

# Human-readable label for each conversational answer key
ANSWER_LABELS = {
    "uses_compact":               "Uses /compact or /clear proactively",
    "context_window_pct":         "Context window under 50%",
    "fresh_conversations":        "Starts fresh conversations per task",
    "log_sharing":                "Points Claude to files on disk (not pasted inline)",
    "image_pasting":              "Does not paste images into chat",
    "model_switching":            "Switches to Haiku/Sonnet for simple tasks",
    "opus_only":                  "Uses Opus only for deep-reasoning tasks",
    "opusplan_known":             "Knows and uses opusplan mode",
    "prompt_quality":             "Writes clear, specific prompts",
    "uses_plan_mode":             "Uses /plan before large tasks",
    "batching":                   "Batches related changes in one conversation",
    "subagent_overuse":           "Does not overuse subagents (uses Grep/Glob instead)",
    "mcp_payloads_reasonable":    "MCP tool call payloads are a reasonable size",
    "checks_cost":                "Uses /cost to monitor spend mid-session",
}

# Scoring lookup: answer value → score
# Scale: 1 = full credit, 0.5 = partial (sometimes/mix), 0 = no credit
# Env signals (in check_env.py) are binary 0/1 — only conversational answers use 0.5.
# Binary questions (no meaningful partial state) stay on 0/1.
ANSWER_SCORE_MAP = {
    #                              yes      partial    no
    "uses_compact":               {"yes": 1, "sometimes": 0.5, "no": 0},
    "context_window_pct":         {"under_50": 1, "50_to_80": 0.5, "over_80": 0, "unsure": 0},
    "fresh_conversations":        {"yes": 1, "sometimes": 0.5, "no": 0},
    "log_sharing":                {"files": 1, "mix": 0.5, "inline": 0},
    "image_pasting":              {"never": 1, "sometimes": 0.5, "often": 0},
    "model_switching":            {"yes": 1, "sometimes": 0.5, "no": 0},
    "opus_only":                  {"yes": 1, "sometimes": 0.5, "no": 0},
    "opusplan_known":             {"yes_use": 1, "yes_know": 0.5, "no": 0},  # use > know > unaware
    "prompt_quality":             {"specific": 1, "mixed": 0.5, "vague": 0},
    "uses_plan_mode":             {"yes": 1, "sometimes": 0.5, "no": 0},
    "batching":                   {"yes": 1, "sometimes": 0.5, "no": 0},
    "subagent_overuse":           {"no": 1, "sometimes": 0.5, "yes": 0},
    "mcp_payloads_reasonable":    {"yes": 1, "sometimes": 0.5, "no": 0},
    "checks_cost":                {"yes": 1, "sometimes": 0.5, "no": 0},
}

ENV_SIGNAL_LABELS = {
    "claudeignore_configured":    "Has .claudeignore configured",
    "claude_md_lean":             "Keeps CLAUDE.md lean (≤200 lines)",
    "mcp_count_reasonable":       "Only necessary MCPs/plugins enabled",
    "permission_mode_non_auto":   "Uses non-auto-accept permission mode",
    "tool_search_efficient":      "Tool Search at efficient default (MCP tools deferred on demand)",
    "memory_populated":           "Caches repeated context in memory",
    "default_model_not_opus":     "Default model set to Sonnet/Haiku (not Opus)",
}

CONTEXT_SIGNAL_LABEL = "context_clean"
CONTEXT_SIGNAL_DESC = "Context baseline is clean (≤15%, no problematic items)"


def _verdict(score, max_score=21):
    # Thresholds scale with max_score. Default 21 = without context (7 env + 14 answers).
    # - Ready: 82%+
    # - Almost There: 55-81%
    # - Building Habits: <55%
    ready_threshold = max_score * 0.82
    needs_improvement_threshold = max_score * 0.55
    if score >= ready_threshold:
        return "Ready"
    elif score >= needs_improvement_threshold:
        return "Almost There"
    return "Building Habits"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", metavar="FILE")
    parser.add_argument("--env-json", metavar="JSON")
    parser.add_argument("--context", metavar="FILE")
    parser.add_argument("--context-json", metavar="JSON")
    parser.add_argument("--answers", metavar="FILE")
    parser.add_argument("--answers-json", metavar="JSON")
    args = parser.parse_args()

    if args.env:
        with open(args.env, encoding="utf-8") as f:
            env_data = json.load(f)
    elif args.env_json:
        env_data = json.loads(args.env_json)
    else:
        print("ERROR: supply --env FILE or --env-json JSON", file=sys.stderr)
        sys.exit(1)

    context_data = None
    if args.context:
        with open(args.context, encoding="utf-8") as f:
            context_data = json.load(f)
    elif args.context_json:
        context_data = json.loads(args.context_json)

    if args.answers:
        with open(args.answers, encoding="utf-8") as f:
            answers = json.load(f)
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

    # Score context signal (if provided)
    context_scored = {}
    if context_data:
        ctx_score = context_data.get("score", 0)
        ctx_fix = ""
        if ctx_score == 0:
            baseline_fix = context_data.get("baseline_fix", "")
            combined_fix = context_data.get("combined_fix", "")
            if baseline_fix and combined_fix:
                ctx_fix = f"{baseline_fix}\n\n{combined_fix}"
            else:
                ctx_fix = baseline_fix or combined_fix or ""
        context_scored[CONTEXT_SIGNAL_LABEL] = {
            "label": CONTEXT_SIGNAL_DESC,
            "score": ctx_score,
            "value": context_data.get("baseline_pct"),
            "fix": ctx_fix,
            "issues": context_data.get("issues", []),
        }

    # Score conversational answers
    answer_scored = {}
    for key, label in ANSWER_LABELS.items():
        raw = answers.get(key, "")
        score = ANSWER_SCORE_MAP.get(key, {}).get(raw, 0)
        answer_scored[key] = {"label": label, "score": score, "value": raw}

    total = (
        sum(s["score"] for s in env_scored.values())
        + sum(s["score"] for s in context_scored.values())
        + sum(s["score"] for s in answer_scored.values())
    )
    max_score = len(env_scored) + len(context_scored) + len(answer_scored)  # 23 with context

    strengths = (
        [s["label"] for s in env_scored.values() if s["score"] == 1]
        + [s["label"] for s in context_scored.values() if s["score"] == 1]
        + [s["label"] for s in answer_scored.values() if s["score"] == 1]
    )[:5]

    red_flags = (
        [
            {"label": s["label"], "fix": s.get("fix", "")}
            for s in env_scored.values()
            if s["score"] == 0
        ]
        + [
            {"label": s["label"], "fix": s.get("fix", "")}
            for s in context_scored.values()
            if s["score"] == 0
        ]
        + [
            {"label": s["label"], "fix": ""}
            for s in answer_scored.values()
            if s["score"] == 0
        ]
    )

    result = {
        "score": total,
        "score_max": max_score,
        "verdict": _verdict(total, max_score),
        "strengths": strengths,
        "red_flags": red_flags,
        "root_cause": answers.get("root_cause", []),
        "env_signals": env_scored,
        "context_signals": context_scored,
        "answer_signals": answer_scored,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
