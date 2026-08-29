"""Contract checks for the documentation-led customer-problem loop."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "apollo-eng" / "skills" / "customer-problem-loop"
SKILL = SKILL_DIR / "SKILL.md"
PLAYBOOK = SKILL_DIR / "references" / "execution-playbook.md"
CHECKPOINTS = SKILL_DIR / "references" / "checkpoint-flow.md"
ATTEMPT_CONTRACT = SKILL_DIR / "references" / "repair-contract.md"

WORD_NUMBERS = {"one": 1, "two": 2, "three": 3}
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.lower().split())


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing section: {heading}"
    return match.group("body")


def _repair_limit() -> int:
    contract = _text(ATTEMPT_CONTRACT)
    match = re.search(r"at most (one|two|three) repair round", contract)
    assert match, "repair limit must be explicit and machine-readable"
    return WORD_NUMBERS[match.group(1)]


@pytest.fixture()
def flow() -> str:
    return _normalized(_section(_text(SKILL), "Checkpoint Flow"))


@pytest.fixture()
def reference() -> str:
    return _normalized(_text(CHECKPOINTS))


@pytest.fixture()
def attempt_contract() -> str:
    return _normalized(_text(ATTEMPT_CONTRACT))


def test_relative_links_resolve() -> None:
    broken: list[str] = []
    for document in (SKILL, *sorted((SKILL_DIR / "references").glob("*.md"))):
        for target in MARKDOWN_LINK_RE.findall(_text(document)):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                broken.append(f"{document.name}: {target}")
    assert not broken, f"unresolvable relative links: {broken}"


def test_skill_frontmatter_remains_valid() -> None:
    lines = _text(SKILL).splitlines()

    assert lines[0] == "---"
    assert lines[1] == "name: customer-problem-loop"
    assert "description:" in lines[2]
    assert "disable-model-invocation: true" in lines[3:6]
    assert "argument-hint: '[problem description or intake link]'" in lines[3:7]
    assert lines[5] == "---"


def test_light_run_example_is_local_and_review_only() -> None:
    usage = _normalized(_section(_text(SKILL), "Usage"))

    assert "run a light local review" in usage
    assert "first build a source-backed problem brief" in usage
    assert "do not implement, push, publish, merge, or contact the customer" in usage


def test_contract_requires_source_backed_problem_understanding() -> None:
    intake = _normalized(_section(_text(SKILL), "Intake"))

    assert "pointer to the underlying request, not as the request itself" in intake
    assert "never scope from only the identifier, title, or summary" in intake
    assert "preserve the customer's words separately from the agent's interpretation" in intake
    assert "bug, feature request, usability gap, outcome gap, or a mixed/unclear problem" in intake
    assert "confirmed facts, customer language, interpretation, and unknowns" in intake
    assert "resolve material ambiguity with targeted questions" in intake


def test_contract_requires_a_right_sized_product_brief() -> None:
    skill = _normalized(_text(SKILL))
    stage_7 = _normalized(_section(_text(PLAYBOOK), "7. Assemble the Product Brief"))

    assert "do not force a one-page limit or pad a simple change" in skill
    assert "there is no one-page target" in stage_7
    assert "keep a narrow change short" in stage_7
    assert "use additional length when evidence" in stage_7


def test_notion_parent_and_stage_six_flag_boundaries_are_explicit() -> None:
    intake = _normalized(_section(_text(SKILL), "Intake"))
    gates = _normalized(_section(_text(SKILL), "Authorization Gates"))
    stage_6 = _normalized(_section(_text(PLAYBOOK), "6. Verify and Capture After Evidence"))
    stage_7 = _normalized(_section(_text(PLAYBOOK), "7. Assemble the Product Brief"))

    assert "confirm its parent page during intake" in intake
    assert "stage 7 must stop before publication" in intake
    assert "read-only beyond the stage-5 flag" in gates
    assert "do not change any flag or permission that stage 5 did not approve" in gates
    assert "do not flip another flag or permission during capture" in stage_6
    assert "parent confirmed during intake" in stage_7
    assert "stop and ask before publishing" in stage_7


def test_checkpoint_flow_blocks_solutioning_until_problem_review_passes(flow, reference) -> None:
    assert "before solutioning" in flow
    assert "a failure blocks approach selection" in flow
    assert "source comprehension" in reference
    assert "current-behavior grounding" in reference
    assert "repair routes back to the problem brief" in reference
    assert "blocked stops downstream work" in reference
    assert (
        "draws one round from the single repair-round budget shared with the approach "
        "and verification checkpoints"
    ) in reference


def test_checkpoint_flow_requires_distinct_alternatives_without_cosmetic_quota(flow, reference) -> None:
    assert "do not manufacture alternatives for a trivial change" in flow
    assert "at least two materially different approaches" in reference
    assert "seek up to four useful approaches" in reference
    assert "fewer than four are acceptable" in reference
    assert "cosmetic or unsupported" in reference
    assert "changes mechanism, ownership boundary, rollout, or risk profile" in reference
    assert (
        "draws from that same shared repair-round budget as the problem and "
        "verification checkpoints"
    ) in reference
    for dimension in (
        "problem fit",
        "repository grounding",
        "assumptions",
        "blast radius",
        "reversibility",
        "testability",
        "operational risk",
    ):
        assert dimension in reference


def test_checkpoint_flow_uses_bounded_independent_review(flow, reference) -> None:
    assert "one primary agent to retain state and ownership" in flow
    assert "reviewers inspect bounded artifacts" in flow
    assert "independent approach-review verdict" in flow
    assert "reviewer does not rewrite the artifacts" in reference


def test_material_plan_changes_require_new_human_approval(flow, reference, attempt_contract) -> None:
    for binding in ("plan revision", "selected approach", "environment", "scope", "side effects", "rollback"):
        assert binding in flow
    assert "invalidates prior approval" in flow
    assert "return here before implementation continues" in reference
    assert "implementation-only repair" in reference
    assert "without another prompt" in reference
    assert (
        "do not repeat an already-satisfied approval unless the plan revision, selected approach, "
        "environment, scope, side effect, or rollback changes"
    ) in attempt_contract


def test_failed_quality_checkpoint_repairs_from_earliest_affected_stage(flow, reference, attempt_contract) -> None:
    assert "a failed checkpoint records the evidence and blocks downstream stages" in flow
    assert "earliest affected stage or checkpoint" in attempt_contract
    assert "repair the same branch and pr" in reference
    assert "every downstream check whose evidence may have changed" in reference


def test_final_handoff_preserves_each_quality_status(flow, reference) -> None:
    stage_9 = _normalized(_section(_text(PLAYBOOK), "9. Hand Off Human Decisions"))

    for status in (
        "problem-review",
        "approach-review",
        "code-quality",
        "solution-quality",
        "verification",
        "human-gate",
    ):
        assert status in flow
    assert "preserve the original verdicts" in stage_9
    assert "cannot convert missing evidence" in reference


def test_attempt_contract_is_bounded_and_reuses_resources(attempt_contract) -> None:
    assert _repair_limit() == 2
    assert "60-minute wall-clock deadline" in attempt_contract
    assert "opaque customer reference" in attempt_contract
    assert "runtime-provided durable evidence location" in attempt_contract
    assert "bind the branch, pr, preview host, and flag target" in attempt_contract
    assert "reuse those bindings for every repair" in attempt_contract
    assert "immediately before the approved flag write" in attempt_contract
    assert "authoritative prior value and rollback" in attempt_contract
    assert (
        "do not restart intake or locate, open a second pr, create a new preview, "
        "recapture an already-valid before state, or repeat an already-applied flag write"
    ) in attempt_contract
    assert "a failed verification records the failed check" in attempt_contract
    assert "proposed change, repair round, and checks to reverify" in attempt_contract


def test_contract_routes_pass_forward_and_failure_to_handoff(attempt_contract) -> None:
    assert "on a pass, continue to the next incomplete stage" in attempt_contract
    assert "after two failed repair rounds" in attempt_contract
    assert "unavailable or ambiguous verification" in attempt_contract
    assert "go directly to stage 9 with a partial handoff" in attempt_contract
    assert "never infer success from missing evidence" in attempt_contract


def test_before_capture_precedes_flag_write() -> None:
    stage_5 = _section(_text(PLAYBOOK), "5. Capture Before and Change the Preview or Staging Flag")
    stage_6 = _section(_text(PLAYBOOK), "6. Verify and Capture After Evidence")

    before = stage_5.index("capture the before screenshot")
    write = stage_5.index("Immediately before writing")
    assert before < write
    assert "flag genuinely off" in stage_5
    assert "Reuse the valid stage-5 before screenshot" in stage_6
    assert "Capture only after and interaction" in stage_6


def test_contract_requires_exact_reviewed_revision() -> None:
    stage_4 = _section(_text(PLAYBOOK), "4. Verify the Preview Environment").lower()

    assert "reviewed pr-head sha" in stage_4
    assert "served revision" in stage_4
    assert "exact match" in stage_4
    assert "stop before stage 5" in stage_4


def test_contract_requires_durable_nonempty_artifacts_without_model_readback() -> None:
    skill = _normalized(_text(SKILL))
    stage_5 = _section(_text(PLAYBOOK), "5. Capture Before and Change the Preview or Staging Flag")
    stage_6 = _section(_text(PLAYBOOK), "6. Verify and Capture After Evidence")

    assert "test -s <path>" in stage_5
    assert "test -s <path>" in stage_6
    assert "non-zero size" in skill
    assert "without reading the image back into model context" in skill
    assert "ephemeral worker is incomplete evidence" in _normalized(stage_6)


def test_contract_requires_pii_and_rollback_safeguards() -> None:
    skill = _normalized(_text(SKILL))
    playbook = _normalized(_text(PLAYBOOK))

    assert "opaque ticket or approved lookup reference" in skill
    assert "raw name, email, and company only inside" in skill
    assert "percent-encodes the email value" in playbook
    assert "preserve the before artifact and rollback across any repair round" in playbook
    assert "pending rollback" in playbook


def test_contract_binds_wait_limits_to_their_stages() -> None:
    stage_4 = _normalized(_section(_text(PLAYBOOK), "4. Verify the Preview Environment"))
    stage_5 = _normalized(
        _section(_text(PLAYBOOK), "5. Capture Before and Change the Preview or Staging Flag")
    )
    stage_6 = _normalized(_section(_text(PLAYBOOK), "6. Verify and Capture After Evidence"))

    assert "10 polls" in stage_4 and "15 minutes" in stage_4
    assert "six checks over two minutes" in stage_5
    assert "five minutes" in stage_6 and "30 seconds" in stage_6


def test_skill_does_not_claim_runtime_enforcement(reference) -> None:
    introduction = _text(SKILL).split("## Usage", 1)[0]

    assert "does not claim" not in introduction.lower()
    assert (
        "does not prove that operator, pantheon, a harness, or any other runtime enforces"
        in reference
    )
    assert "state persistence, reviewer isolation, repair routing, or human gates" in reference
