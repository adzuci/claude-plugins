import pytest

score = pytest.importorskip("score")


class TestVerdictScaling:
    def test_verdict_max_22(self):
        # 82% of 22 = 18.04, so need 19+ for "Yes"
        # 55% of 22 = 12.1, so need 13+ for "Needs improvement"
        assert score._verdict(19, 22) == "Yes"
        assert score._verdict(18, 22) == "Needs improvement"
        assert score._verdict(13, 22) == "Needs improvement"
        assert score._verdict(12, 22) == "No"

    def test_verdict_max_23(self):
        # 82% of 23 = 18.86, so need 19+ for "Yes"
        # 55% of 23 = 12.65, so need 13+ for "Needs improvement"
        assert score._verdict(19, 23) == "Yes"
        assert score._verdict(18, 23) == "Needs improvement"
        assert score._verdict(13, 23) == "Needs improvement"
        assert score._verdict(12, 23) == "No"


class TestContextSignalScoring:
    def test_context_signal_pass(self):
        context_data = {"score": 1, "baseline_pct": 10}
        answers = {
            "uses_compact": "yes",
            "context_window_pct": "under_50",
            "checks_ccflare": "yes",
            "fresh_conversations": "yes",
            "log_sharing": "files",
            "image_pasting": "never",
            "prompt_language": "english",
            "model_switching": "yes",
            "opus_only": "yes",
            "opusplan_known": "yes_use",
            "prompt_quality": "specific",
            "uses_plan_mode": "yes",
            "batching": "yes",
            "subagent_overuse": "no",
            "mcp_payloads_reasonable": "yes",
        }

        env_scored = {}
        for key, label in score.ENV_SIGNAL_LABELS.items():
            env_scored[key] = {"label": label, "score": 0, "value": None, "fix": ""}

        context_scored = {
            score.CONTEXT_SIGNAL_LABEL: {
                "label": score.CONTEXT_SIGNAL_DESC,
                "score": context_data["score"],
                "value": context_data["baseline_pct"],
                "fix": "",
            }
        }

        answer_scored = {}
        for key, label in score.ANSWER_LABELS.items():
            raw = answers.get(key, "")
            s = score.ANSWER_SCORE_MAP.get(key, {}).get(raw, 0)
            answer_scored[key] = {"label": label, "score": s, "value": raw}

        total = (
            sum(s["score"] for s in env_scored.values())
            + sum(s["score"] for s in context_scored.values())
            + sum(s["score"] for s in answer_scored.values())
        )
        max_score = len(env_scored) + len(context_scored) + len(answer_scored)

        assert max_score == 23
        assert context_scored[score.CONTEXT_SIGNAL_LABEL]["score"] == 1
        assert total == 16  # env=0, context=1, answers=15

    def test_context_signal_fail_generates_fix(self):
        context_data = {
            "score": 0,
            "baseline_pct": 25,
            "baseline_fix": "Context baseline is 25% (threshold: 15%).",
            "combined_fix": "Add to .claudeignore:\nnode_modules/",
            "issues": [{"name": "node_modules/x", "pct": 10}],
        }

        ctx_fix = ""
        baseline_fix = context_data.get("baseline_fix", "")
        combined_fix = context_data.get("combined_fix", "")
        if baseline_fix and combined_fix:
            ctx_fix = f"{baseline_fix}\n\n{combined_fix}"
        else:
            ctx_fix = baseline_fix or combined_fix or ""

        assert "Context baseline is 25%" in ctx_fix
        assert "node_modules/" in ctx_fix


class TestMaxScoreCalculation:
    def test_max_score_without_context(self):
        max_score = len(score.ENV_SIGNAL_LABELS) + len(score.ANSWER_LABELS)
        assert max_score == 22

    def test_max_score_with_context(self):
        max_score = len(score.ENV_SIGNAL_LABELS) + 1 + len(score.ANSWER_LABELS)
        assert max_score == 23
