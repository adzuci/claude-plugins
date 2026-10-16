from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugins" / "apollo-product-lab"
INVENTORY = PLUGIN / "skills" / "design-diff" / "scripts" / "inventory.py"
APPEND = PLUGIN / "framework" / "ledger" / "append.py"


def run(*args, cwd=None, env=None):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run([sys.executable, *map(str, args)], cwd=cwd or REPO, env=merged, capture_output=True, text=True)


def _git_repo(path: Path, branch: str = "prototype/x"):
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"], cwd=path, check=True)


def test_inventory_refuses_missing_dirs_and_phantom_exclusions(tmp_path):
    proto = tmp_path / "proto"; prod = tmp_path / "prod"
    _git_repo(proto); _git_repo(prod, "master")
    assert run(INVENTORY, tmp_path / "nope", prod).returncode == 2
    assert run(INVENTORY, proto, prod, "--exclude", "ghost").returncode == 2
    assert run(INVENTORY, proto, prod, "--expect-branch", "master").returncode == 2


def test_inventory_records_revisions_and_declared_exclusions(tmp_path):
    proto = tmp_path / "proto"; prod = tmp_path / "prod"
    _git_repo(proto); _git_repo(prod, "master")
    (proto / "components").mkdir(); (proto / "lists").mkdir()
    (proto / "components" / "SyncCard.tsx").write_text("import { Card } from '@apolloio/fabric-core';\nexport default () => <Card>Sync created</Card>;\n")
    (proto / "lists" / "ListPage.tsx").write_text("export default () => <div>Lists</div>;\n")
    (prod / "SyncCard.tsx").write_text("import { Card } from '@apolloio/fabric-core';\nexport default () => <Card/>;\n")
    (prod / "Other.tsx").write_text("export default () => null;\n")
    out = tmp_path / "inv.md"
    r = run(INVENTORY, proto, prod, "--exclude", "lists", "--expect-branch", "prototype/x", "--out", out)
    assert r.returncode == 0, r.stderr
    text = out.read_text()
    assert "branch `prototype/x`" in text and "branch `master`" in text
    assert "Exclusions (declared by the caller, none inferred): `lists`" in text
    assert "ListPage" not in text
    assert "`SyncCard.tsx`" in text and "candidate pair above" in text
    assert "`Other.tsx`" in text  # never dropped from the production list
    assert "'Sync created'" in text


def test_append_validates_and_refuses_duplicates(tmp_path):
    env = {"HARNESS_REPO_ROOT": str(tmp_path)}
    base = [APPEND, "demo", "--run", "demo-run1", "--event", "e001-x", "--stage", "F.build", "--agent", "a", "--outcome", "resolved-clean", "--evidence", "x.md"]
    r = run(*base, env=env); assert r.returncode == 0, r.stderr
    rec = json.loads((tmp_path / ".ai" / "demo" / "ledger.jsonl").read_text().splitlines()[0])
    assert rec["evidence"] == ["x.md"] and rec["task_class"] == "F.build"
    assert run(*base, env=env).returncode == 1  # duplicate event id
    assert run(*base, "--force", env=env).returncode == 0
    bad = list(base); bad[bad.index("F.build")] = "bogus"; bad[bad.index("e001-x")] = "e002-y"
    assert run(*bad, env=env).returncode == 1
    council = list(base); council[council.index("F.build")] = "council.adr-p3"; council[council.index("e001-x")] = "e003-z"
    assert run(*council, env=env).returncode == 0


RECORD_SYNC = PLUGIN / "scripts" / "record-sync.sh"
RECORD_WRITERS = [
    "skills/harness-snapshot/SKILL.md",
    "skills/harness-council/SKILL.md",
    "skills/harness-intake/SKILL.md",
    "skills/product-harness-init/SKILL.md",
    "skills/design-diff/SKILL.md",
    "skills/artifact-audit/SKILL.md",
    "agents/product-orchestrator.md",
]


def test_every_record_writer_shares_through_record_sync():
    for rel in RECORD_WRITERS:
        assert "record-sync.sh" in (PLUGIN / rel).read_text(), rel


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _seed_repo(tmp_path, collaboration):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(remote), str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "checkout", "-q", "-b", "WO-1/harness-artifacts")
    (repo / ".ai" / "demo").mkdir(parents=True)
    (repo / ".ai" / "demo" / "ledger.jsonl").write_text("")
    (repo / ".ai" / "harness-profile.yml").write_text(f"persona: engineer\ncollaboration: {collaboration}\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "push", "-q", "-u", "origin", "WO-1/harness-artifacts")
    return remote, repo


def _sync(repo, *args):
    return subprocess.run(
        ["bash", str(RECORD_SYNC), *args], cwd=repo, capture_output=True, text=True,
        env={**os.environ, "HARNESS_REPO_ROOT": str(repo), "HOME": str(repo.parent / "nohome")},
    )


def test_record_sync_is_a_noop_for_solo(tmp_path):
    _, repo = _seed_repo(tmp_path, "solo")
    (repo / ".ai" / "demo" / "note.md").write_text("x")
    r = _sync(repo, "push", "demo", "msg")
    assert r.returncode == 0 and "solo" in r.stdout
    assert "note.md" in _git(repo, "status", "--short")


def test_record_sync_pushes_for_team_and_refuses_master(tmp_path):
    remote, repo = _seed_repo(tmp_path, "team")
    (repo / ".ai" / "demo" / "runs").mkdir()
    (repo / ".ai" / "demo" / "runs" / "a.snapshot.md").write_text("snap")
    r = _sync(repo, "push", "demo", "demo: snapshot")
    assert r.returncode == 0, r.stderr
    assert "a.snapshot.md" in _git(remote, "show", "--stat", "--format=", "WO-1/harness-artifacts")
    _git(repo, "checkout", "-q", "-b", "master")
    r = _sync(repo, "push", "demo", "msg")
    assert r.returncode == 2 and "refusing" in r.stderr


AI_OPPORTUNITY_CARRIERS = [
    "framework/42-ai-opportunity-lens.md",
    "framework/templates/ai-opportunities.md",
    "framework/34-harness-council.md",
    "framework/17-decide-stage.md",
    "skills/harness-intake/SKILL.md",
    "skills/harness-council/SKILL.md",
    "agents/product-orchestrator.md",
    "agents/product-reviewer.md",
    "framework/models/model-registry.yml",
]


def test_ai_opportunity_lens_is_wired_with_a_human_go_ahead():
    for rel in AI_OPPORTUNITY_CARRIERS:
        text = (PLUGIN / rel).read_text()
        assert "opportunit" in text.lower(), rel
    doc = (PLUGIN / "framework/42-ai-opportunity-lens.md").read_text()
    for word in ("now", "next version", "never", "deferred", "rejected", "accepted"):
        assert word in doc
    assert "find.opportunity.ai" in (PLUGIN / "framework/models/model-registry.yml").read_text()


PLATFORM_LENS_CARRIERS = [
    "framework/47-platform-lens.md",
    "framework/templates/platform-opportunities.md",
    "framework/34-harness-council.md",
    "framework/17-decide-stage.md",
    "framework/36-roles-quickstart.md",
    "framework/index.md",
    "skills/harness-intake/SKILL.md",
    "skills/harness-council/SKILL.md",
    "agents/product-orchestrator.md",
    "agents/product-reviewer.md",
    "framework/models/model-registry.yml",
]


def test_platform_lens_is_conditional_wired_and_needs_a_human_go_ahead():
    for rel in PLATFORM_LENS_CARRIERS:
        assert "doc 47" in (PLUGIN / rel).read_text() or rel.startswith(("framework/47", "framework/index", "framework/models")), rel
    doc = (PLUGIN / "framework/47-platform-lens.md").read_text()
    assert doc.startswith("# 47") and "Decision 2026-10-12 (Akansh)" in doc
    for word in ("feature parity", "shared flow", "shared backend", "platformize now", "never", "skipped",
                 "router defect", "B.platform-opportunity", "find.opportunity.platform", "doc 43", "unverified"):
        assert word in doc, word
    assert "](./47-platform-lens.md)" in (PLUGIN / "framework/index.md").read_text()
    registry = (PLUGIN / "framework/models/model-registry.yml").read_text()
    role = [l for l in registry.splitlines() if l.strip().startswith("find.opportunity.platform:")]
    assert len(role) == 1 and "product-reviewer (platform mode)" in role[0] and "sibling check" in role[0]
    template = (PLUGIN / "framework/templates/platform-opportunities.md").read_text()
    for word in ("proposed", "accepted", "deferred", "rejected", "feature parity", "shared flow", "shared backend", "Owning-team answer"):
        assert word in template, word
    council = (PLUGIN / "framework/34-harness-council.md").read_text()
    row = [l for l in council.splitlines() if l.startswith("| Platform (conditional)")]
    assert len(row) == 1 and "find.opportunity.platform" in row[0] and "only when" in row[0] and "skip" in row[0]
    skill = (PLUGIN / "skills/harness-council/SKILL.md").read_text()
    assert "platform lens" in skill and "only when the intake's quick sibling check" in skill
    orchestrator = (PLUGIN / "agents/product-orchestrator.md").read_text()
    rule = orchestrator.split("Platform rows are proposed")[1].split("\n")[0]
    assert "`accepted` by a named human" in rule and "owning team's answer is recorded" in rule and "router defect" in rule


def test_cross_role_review_matrix_peer_design_ux_research_and_feasibility_are_wired():
    council = (PLUGIN / "framework/34-harness-council.md").read_text()
    matrix = council.split("### 2b. Cross-role review matrix", 1)[1].split("\n## 3.", 1)[0]
    rows = {l.split("|")[1].strip(): l for l in matrix.splitlines() if l.startswith("| ") and "(`" in l.split("|")[1]}
    assert "design, engineering feasibility, UX research" in rows["PRD (`prd`)"]
    assert "product, peer design, UX research, engineering feasibility" in rows["Design (`design`)"]
    for kind in ("ERD / plan (`erd`, `plan`)", "PR (`pr`)"):
        assert "product, design, QA" in rows[kind], kind
    for word in ("Pre-work briefs", "Size rules still", "peer PM is the Product lens", "peer design lens fills that gap",
                 "never the code", "`feature-qa-wizard`", "`qa-steps-for-eng`", "`design-diff`", "from the decided version"):
        assert word in matrix, word
    registry = (PLUGIN / "framework/models/model-registry.yml").read_text()
    reviewer = (PLUGIN / "agents/product-reviewer.md").read_text()
    for lens, role, mode in (("| Peer design |", "decide.design.peer:", "Peer-design mode"),
                             ("| UX research |", "decide.research.ux-evidence:", "UX-research mode"),
                             ("| Engineering feasibility |", "decide.feasibility.engineering:", None)):
        assert lens in council and role.rstrip(":") in council and role in registry, role
        if mode:
            assert mode in reviewer, mode
    assert "never re-runs discovery" in council and "never re-run discovery" in reviewer
    find = (PLUGIN / "framework/16-find-stage.md").read_text()
    reachable = find.split("**Reachable now:**", 1)[1].split("**Not authenticated:**", 1)
    for tool in ("get_graph_schema", "search_graph_values", "run_graph_query", "find_user_quote"):
        assert tool in reachable[0], tool
    assert "Enterpret" not in reachable[1].split("\n", 1)[0]
    quick = (PLUGIN / "framework/36-roles-quickstart.md").read_text()
    assert "## Who reviews your work, and the brief you get first" in quick
    assert "Pre-work brief" in (PLUGIN / "skills/harness-council/SKILL.md").read_text()


def test_generic_plugin_carries_no_run_specific_replay_fixtures():
    assert not (PLUGIN / "framework/eval/replay/arun-ads-be-2026-10").exists()
    assert (PLUGIN / "framework/eval/replay/cases.schema.json").exists()
    for path in PLUGIN.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".yml", ".json", ".py"):
            assert "arun-ads-be-2026-10" not in path.read_text(errors="ignore"), path


def test_host_path_cost_rule_columns_lens_and_escape_record():
    patterns = (PLUGIN / "framework/apollo-infra-patterns.md").read_text()
    ip18 = patterns.split("## IP18.", 1)[1].split("\n## ", 1)[0].split("\n---", 1)[0]
    assert "costs nothing for a team that does not use the feature" in ip18
    for part in ("- **Pattern.**", "- **Do.**", "- **Don't.**", "- **Check.**", "in-process gate", "host peak", "measured peak"):
        assert part in ip18, part
    assert "| IP18 |" in patterns
    assert "per shared resource, not per row" in ip18 and "coincident host peaks" in ip18
    assert "summed at coincident host peaks" in (PLUGIN / "framework/templates/erd.md").read_text()
    assert "sum the projected increase" in (PLUGIN / "agents/infra-lens.md").read_text()
    for rel in ("framework/17-decide-stage.md", "framework/templates/erd.md"):
        text = (PLUGIN / rel).read_text()
        for col in ("peak calls/s", "not us", "using it" if rel.endswith("erd.md") else "one that does",
                    "shared resource", "measured peak", "projected increase", "metric"):
            assert col.lower() in text.lower(), (rel, col)
        assert "`[assumed]` is allowed only with" in " ".join(text.split()), rel
    council = (PLUGIN / "framework/34-harness-council.md").read_text()
    infra = [l for l in council.splitlines() if l.startswith("| Infra (be-platform)")][0]
    assert "IP18" in infra and "Grafana" in infra and "`unverified`" in infra and "pre-merge human check" in infra
    lens = (PLUGIN / "agents/infra-lens.md").read_text()
    assert "IP1 to IP18" in lens and "host rate" in lens and "`unverified`" in lens
    verify = (PLUGIN / "framework/21-verify-stage.md").read_text()
    assert "## 8c. Re-check host-path cost against live metrics before merge" in verify and "does not pass on the design's\nnumbers alone" in verify and "§8c" in verify.split("G5a")[1]
    esc = PLUGIN / "framework/eval/escapes/2026-10-12-ads-hook-host-path-cost.md"
    text = esc.read_text()
    for section in ("id: ads-builder-hook-cost-1", "kind: retrospective", "## Finding", "## Owning stage", "## Why it was missed", "## Fix",
                    "Retrospective case, not replay"):
        assert section in text, section
    assert "/Users/" not in text and ".ai/" not in text
    assert esc.name in (PLUGIN / "framework/eval/escapes/README.md").read_text()


def test_ads_m1_learning_docs_and_stale_reviews_are_folded_and_removed():
    fw = PLUGIN / "framework"
    for gone in ("30-pilot-learnings-ads-m1.md", "31-ads-m1-build-learnings.md", "reviews/astra-2026-09-19.md",
                 "reviews/astra-2026-09-19.status.md", "reviews/team-feedback-2026-09-21.md"):
        assert not (fw / gone).exists(), gone
    assert (fw / "reviews/glean-adversary-probe-2026-09-22.md").exists()
    for path in PLUGIN.rglob("*.md"):
        text = path.read_text()
        for ref in ("30-pilot-learnings", "31-ads-m1-build", "astra-2026-09-19", "team-feedback-2026-09-21"):
            assert ref not in text, (path, ref)
    for rel, rule in (("14-orchestration.md", "Trust the artifact, not the report"), ("14-orchestration.md", "One product, one home"),
                      ("26-authority-policy.md", "Read back after every outward action"), ("37-model-bridge-and-context-budget.md", "Tool read caps"),
                      ("17-decide-stage.md", "Lead with options, never with a question"), ("21-verify-stage.md", "Runtime verification is a gate"),
                      ("20-build-stage.md", "Preflight every new artifact type"), ("20-build-stage.md", "is-ancestor"), ("20-build-stage.md", "LEFTHOOK=0"),
                      ("20-build-stage.md", "<Worker>.perform_async"), ("20-build-stage.md", "Exit code 124"),
                      ("17-decide-stage.md", "[P]-sourced before DECIDE closes"), ("17-decide-stage.md", "scale posture table"),
                      ("17-decide-stage.md", "new version, not an edit in place"), ("14-orchestration.md", "neither trusted nor rejected blindly"),
                      ("46-build-and-review-loop-budget.md", "one\nafter the other")):
        assert rule in (fw / rel).read_text(), (rel, rule)


def test_shipped_connectors_and_shunt_skill():
    mcp = json.loads((PLUGIN / ".mcp.json").read_text())["mcpServers"]
    for name in ("notion", "atlassian", "slack", "glean", "figma", "claude-design", "sentry", "amplitude", "grafana"):
        assert name in mcp, name
    assert "playwright" not in mcp and all(cfg["type"] == "http" for cfg in mcp.values())
    for name, cfg in mcp.items():
        assert cfg.get("type") in ("http", "stdio"), name
        if cfg["type"] == "http":
            assert cfg["url"].startswith("https://"), name
    skill = (PLUGIN / "skills/harness-shunt/SKILL.md").read_text()
    desc = [l for l in skill.splitlines() if l.startswith("description:")][0]
    assert "<" not in desc
    for word in ("settings.json", "Desktop", "off"):
        assert word in skill


def test_shunt_template_sets_effort_per_route_not_provider():
    template = (PLUGIN / "framework/models/shunt.toml.example").read_text()
    assert 'model = "gpt-6-astra"\nprovider = "codex"\neffort = "xhigh"' in template
    assert 'model = "gpt-5.6-sol"' in template and 'effort = "medium"' in template
    provider = template.split("[providers.codex]", 1)[1].split("[", 1)[0]
    assert "effort" not in provider
    doc = (PLUGIN / "framework/48-reuse-first-and-implementation-models.md").read_text()
    assert "route, then provider, then the request's effort, then thinking enabled (high)" in doc
    assert "https://shunt.sh/guides/effort-and-context/" in doc


def test_second_family_is_installed_by_default_for_non_design_personas():
    onboard = (PLUGIN / "skills/harness-onboard/SKILL.md").read_text()
    assert "openai/codex-plugin-cc" in onboard and "harness-shunt setup" in onboard
    assert "declined" in onboard
    shunt = (PLUGIN / "skills/harness-shunt/SKILL.md").read_text()
    assert "codex@openai-codex" in shunt and "review gate" in shunt
    assert "second_family:" in (PLUGIN / "framework/templates/harness-profile.yml").read_text()
    hook = (PLUGIN / "scripts/session-start.sh").read_text()
    assert "second_family" in hook and "designer" in hook


def test_context_and_model_precedence_guidance_is_present():
    doc = (PLUGIN / "framework/37-model-bridge-and-context-budget.md").read_text()
    for word in ("autocompact", "model_auto_compact_token_limit", "record and a recommendation", "codex exec -c model_reasoning_effort=xhigh"):
        assert word in doc, word
    hook = (PLUGIN / "scripts/session-start.sh").read_text()
    assert '"compact"' in hook and "index.md" in hook and "snapshot.md" in hook
    out = subprocess.run(["bash", str(PLUGIN / "scripts/session-start.sh")], input='{"source":"compact"}', capture_output=True, text=True, env={**os.environ, "HOME": str(PLUGIN.parent)}).stdout
    assert "No harness profile" in out or "compacted" in out


def test_notion_page_is_part_of_every_human_facing_write():
    assert "notion:" in (PLUGIN / "framework/templates/stage-snapshot.md").read_text()
    snap = (PLUGIN / "skills/harness-snapshot/SKILL.md").read_text()
    assert "Not optional" in snap and "notion:" in snap
    council = (PLUGIN / "skills/harness-council/SKILL.md").read_text()
    assert "Notion page for the memo" in council
    assert "notion:" in (PLUGIN / "scripts/record-sync.sh").read_text()


SESSION_START = PLUGIN / "scripts" / "session-start.sh"


def _hook(cwd, home, source="startup"):
    return subprocess.run(
        ["bash", str(SESSION_START)], cwd=cwd, input=json.dumps({"source": source}), capture_output=True, text=True,
        env={**os.environ, "HOME": str(home), "CLAUDE_PLUGIN_ROOT": str(PLUGIN)},
    ).stdout


def _profile(home, text):
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "harness-profile.yml").write_text(text)


def test_session_start_reads_only_and_prints_the_loaded_version(tmp_path):
    hook = SESSION_START.read_text()
    assert "git pull" not in hook.split("\n", 4)[-1] and "--max-time 1" in hook
    version = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())["version"]
    empty = tmp_path / "empty"
    empty.mkdir()
    sha = subprocess.run(["git", "-C", str(PLUGIN), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert f"[apollo-product-lab {version} build {sha}]" in _hook(empty, empty)
    home = tmp_path / "home"
    _profile(home, "persona: designer\ncollaboration: team\n")
    out = _hook(empty, home)
    assert "no-repo mode" in out and "shunt" not in out and "team mode" not in out


def test_session_start_after_compaction_is_bounded_and_only_for_a_bound_run(tmp_path):
    home = tmp_path / "home"
    _profile(home, "persona: engineer\ncollaboration: team\ndefault_run: demo-run1\nsecond_family: declined 2026-10-01\n")
    repo = tmp_path / "repo"
    _git_repo(repo)
    rundir = repo / ".ai" / "demo" / "runs" / "demo-run1"
    rundir.mkdir(parents=True)
    (rundir / "index.md").write_text("| x |\n")
    rows = "".join(f"| check {i} | checked | e |\n" for i in range(30))
    (rundir / "D.design.snapshot.md").write_text(f"---\nstage: D.design\ngate_status: open\n---\n\n## Checks\n| Check | Pass/Fail | Evidence |\n|---|---|---|\n{rows}")
    out = _hook(repo, home, "compact").splitlines()
    assert out[0].endswith("the record on disk is authoritative (doc 37 §3b).") and len(out) <= 16
    assert "stage: D.design" in out and not any("write its snapshot" in line for line in out)
    other = tmp_path / "other"
    _git_repo(other)
    (other / ".ai").mkdir()
    assert "compacted" not in _hook(other, home, "compact")


def test_record_sync_refuses_to_pull_over_local_record_edits(tmp_path):
    _, repo = _seed_repo(tmp_path, "team")
    (repo / ".ai" / "demo" / "ledger.jsonl").write_text("local edit\n")
    r = _sync(repo, "pull", "demo")
    assert r.returncode == 2 and "refusing to pull" in r.stderr
    assert (repo / ".ai" / "demo" / "ledger.jsonl").read_text() == "local edit\n"
    plain = tmp_path / "plain"
    plain.mkdir()
    r = subprocess.run(["bash", str(RECORD_SYNC), "pull", "demo"], cwd=plain, capture_output=True, text=True,
                       env={**os.environ, "HARNESS_REPO_ROOT": str(plain), "HOME": str(tmp_path / "nohome")})
    assert r.returncode == 0 and "no-repo mode" in r.stdout


def test_learning_loop_is_wired():
    doc = (PLUGIN / "framework/43-learning-loop-and-review-defaults.md").read_text()
    for word in ("retrospective case, not replay", "Harness run: <initiative>/<run-id>", "highest trigger wins", "No-repo mode"):
        assert word.lower() in doc.lower(), word
    escape = (PLUGIN / "skills/harness-escape/SKILL.md").read_text()
    assert "disable-model-invocation: true" in escape and "never edits a rule" in escape
    for rel in ("skills/harness-intake/SKILL.md", "skills/harness-snapshot/SKILL.md"):
        assert "skills/harness-escape/SKILL.md" in (PLUGIN / rel).read_text(), rel
    assert "H.escape" in (PLUGIN / "agents/product-orchestrator.md").read_text()
    assert "No local file paths" in (PLUGIN / "framework/templates/notion-page.md").read_text()
    assert "multi-step build task" not in (PLUGIN / "skills/harness-snapshot/SKILL.md").read_text().split("---")[1]


def test_session_start_resolves_the_repo_root_from_a_subfolder(tmp_path):
    home = tmp_path / "home"
    _profile(home, "persona: engineer\ncollaboration: solo\ndefault_run: demo-run1\nsecond_family: declined 2026-10-01\n")
    repo = tmp_path / "repo"
    _git_repo(repo)
    fresh = _hook(repo, home)
    assert "not initialised" in fresh and "no-repo" not in fresh
    rundir = repo / ".ai" / "demo" / "runs" / "demo-run1"
    rundir.mkdir(parents=True)
    (repo / ".ai" / "demo" / "harness-manifest.md").write_text("x\n")
    (rundir / "index.md").write_text("| x |\n")
    (rundir / "A.audit.snapshot.md").write_text("---\nstage: A.audit\n---\n")
    sub = repo / "packs"
    sub.mkdir()
    out = _hook(sub, home)
    assert "no-repo" not in out and "not initialised" not in out and "initiatives here: demo" in out
    assert "stage: A.audit" in _hook(sub, home, "compact")


def test_record_sync_refuses_to_push_unrelated_staged_files(tmp_path):
    _, repo = _seed_repo(tmp_path, "team")
    (repo / "app.rb").write_text("x\n")
    _git(repo, "add", "app.rb")
    (repo / ".ai" / "demo" / "note.md").write_text("x\n")
    r = _sync(repo, "push", "demo", "demo: note")
    assert r.returncode == 2 and "app.rb" in r.stderr
    assert "app.rb" in _git(repo, "diff", "--cached", "--name-only")


def test_connector_list_is_tracked_and_ships_in_the_archive():
    ignored = subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", str(PLUGIN / ".mcp.json")])
    assert ignored.returncode == 1
    text = (PLUGIN / ".mcp.json").read_text()
    for word in ("token", "secret", "Bearer", "api_key"):
        assert word.lower() not in text.lower(), word


def test_no_one_file_shortcut_remains():
    for rel in ("skills/harness-council/SKILL.md", "skills/harness-snapshot/SKILL.md", "agents/product-orchestrator.md",
                "framework/40-work-sizes.md", "framework/34-harness-council.md"):
        text = (PLUGIN / rel).read_text()
        assert "one-file change with no decision" not in text and "one file with no decision" not in text, rel
        assert "demonstrated low risk" in text, rel



LOOP_BUDGET = "framework/46-build-and-review-loop-budget.md"


def _text(rel):
    return (PLUGIN / rel).read_text()


def test_loop_budget_pins_the_caps():
    doc = _text(LOOP_BUDGET)
    for phrase in (
        "`docker exec`", "never a fresh container per run", "only when an index definition changed",
        "`SKIP_COVERAGE=1 bin/rspec", "`RSPEC_CREATE_MONGO_INDEXES=1` only on the first run after an index change",
        "`ci-speed-run`", "only the affected specs", "**once**, before the commit", "Fix loops after a review run affected specs only",
        "Only on behaviour changes", "Target 10 mutants or fewer", "More\nthan 10 is a named breach",
        "against its own spec file only", "re-run only the mutants",
        "**Pass 2** reviews the delta only", "**If pass 2 still has blockers, stop.** Do not run a pass 3",
        "a human explicitly asks", "together are one pass", "takes that pass's slot",
        "No pasted file bodies", "15,000 characters or fewer", "--prompt-chars", "Loop report: build",
    ):
        assert phrase in doc.replace("\n   ", "\n"), phrase


def test_loop_budget_reaches_every_build_and_review_entry_point():
    required = {
        "framework/20-build-stage.md": ("doc 46", "`docker exec`", "only affected specs", "at most 10 mutants", "Cross-family review is two passes at most"),
        "framework/34-harness-council.md": ("doc 46 §4", "pass 2 on\n  the delta only", "together are one pass", "15,000 characters"),
        "framework/43-learning-loop-and-review-defaults.md": ("At most two passes per artifact", "prompt characters"),
        "framework/44-dispatch-rule.md": ("doc 46 §4 and §5", "no pasted file bodies", "15,000 characters", "--prompt-chars"),
        "framework/17-decide-stage.md": ("two passes per design", "no pasted file bodies"),
        "framework/index.md": ("46-build-and-review-loop-budget.md",),
        "framework/templates/stage-snapshot.md": ("## Loop report", "Loop report: build"),
        "skills/harness-intake/SKILL.md": ("doc 46", "never a fresh", "at most 10 mutants", "behaviour changes only", "two cross-family passes"),
        "skills/harness-council/SKILL.md": ("pr, design and erd kind", "no pass 3 unless a human explicitly asks", "15,000 characters", "together are one pass"),
        "skills/harness-snapshot/SKILL.md": ("**Loop report**", "--prompt-chars"),
        "agents/product-orchestrator.md": ("slice-owner and fix brief", "`docker exec`", "at most 10 mutants", "at most two cross-family review passes"),
    }
    for rel, phrases in required.items():
        text = _text(rel)
        for phrase in phrases:
            assert phrase in text, (rel, phrase)
    legacy = {
        "framework/17-decide-stage.md": ("at most four reviews", "with the artifact on stdin"),
        "skills/harness-council/SKILL.md": ("One review per `design_sha` plus one re-review", "tech-lead synthesizer), then `/codex:adversarial-review`", "chunking above ~6k words"),
    }
    for rel, phrases in legacy.items():
        for phrase in phrases:
            assert phrase not in _text(rel), (rel, phrase)


def test_append_records_minutes_and_prompt_size(tmp_path):
    env = {"HARNESS_REPO_ROOT": str(tmp_path)}
    base = [APPEND, "demo", "--run", "demo-run1", "--stage", "council.pr-42", "--agent", "council.adversary", "--outcome", "resolved-clean"]
    r = run(*base, "--event", "e1", "--tokens", "120000", "--minutes", "7.5", "--prompt-chars", "14200", env=env)
    assert r.returncode == 0, r.stderr
    r = run(*base, "--event", "e2", "--minutes", "0", "--prompt-chars", "0", env=env)
    assert r.returncode == 0, r.stderr
    lines = (tmp_path / ".ai" / "demo" / "ledger.jsonl").read_text().splitlines()
    rec = json.loads(lines[0])
    assert rec["minutes"] == 7.5 and rec["prompt_chars"] == 14200 and rec["tokens"] == 120000
    assert json.loads(lines[1])["minutes"] == 0
    for event, flag, value, msg in (("e3", "--minutes", "-1", "minutes below 0"), ("e4", "--minutes", "nan", "finite"),
                                    ("e5", "--minutes", "inf", "finite"), ("e6", "--prompt-chars", "-5", "prompt_chars below 0")):
        r = run(*base, "--event", event, flag, value, env=env)
        assert r.returncode == 1 and msg in r.stderr, (flag, value, r.stderr)
    assert run(*base, "--event", "e7", "--prompt-chars", "1.5", env=env).returncode == 2
    assert len((tmp_path / ".ai" / "demo" / "ledger.jsonl").read_text().splitlines()) == 2
    sys.path.insert(0, str(APPEND.parent))
    import importlib
    append_mod = importlib.import_module("append")
    assert any("must be an integer" in e for e in append_mod.validate({"prompt_chars": True}))
    assert any("finite" in e for e in append_mod.validate({"minutes": True}))


BUILD = "framework/20-build-stage.md"


def _read(rel):
    return (PLUGIN / rel).read_text()


def _frontmatter_tools(text):
    lines = text.split("---", 2)[1].splitlines()
    start = next((index for index, line in enumerate(lines) if line.startswith("tools:")), None)
    assert start is not None, "agent must declare tools in frontmatter"
    fragment = [lines[start]]
    for line in lines[start + 1:]:
        if line and not line[0].isspace():
            break
        fragment.append(line)
    return yaml.safe_load("\n".join(fragment))["tools"]


def _tool_names(value):
    if isinstance(value, str):
        return {name.strip() for name in value.split(",") if name.strip()}
    if isinstance(value, list):
        assert all(isinstance(name, str) for name in value), "tools list entries must be strings"
        return {name.strip() for name in value if name.strip()}
    raise AssertionError("tools must be a YAML list or comma-separated string")


def test_pr_size_rule_is_15_target_30_cap_everywhere():
    build = _read(BUILD)
    assert "15 files is the target, 30 is the cap" in build
    assert "gh pr diff <n> --name-only" in build
    for rel in ("agents/slice-integrator.md", "skills/harness-intake/SKILL.md", "skills/harness-council/SKILL.md"):
        text = _read(rel)
        assert "15" in text and "30" in text and "doc 20 §8b" in text, rel
    assert "gh pr diff <n> --name-only" in _read("agents/slice-integrator.md")
    assert "gh pr diff <n> --name-only" in _read("skills/harness-council/SKILL.md")


def test_old_40_file_rule_is_gone():
    for path in PLUGIN.rglob("*"):
        if path.is_file() and path.suffix in (".md", ".yml", ".yaml", ".json", ".sh"):
            text = path.read_text()
            assert "~40 files" not in text and "40 files" not in text, path.relative_to(PLUGIN)


def test_px0_is_opt_in_and_pinned_for_code_reviewers_only():
    onboard = _read("skills/harness-onboard/SKILL.md")
    assert "brew install px0" in onboard
    assert "PX0_VERSION=" in onboard and "PX0_SHA256=" in onboard
    assert "PX0_REPORTED_VERSION=$(px0 -version" in onboard
    assert 'VERSION="$PX0_VERSION" sh "$tmp/install.sh"' in onboard
    assert "opt-in" in onboard
    assert "Security" in onboard
    assert "Never install it for a designer or UX persona" in onboard
    assert "px0:" in _read("framework/templates/harness-profile.yml")
    assert any(line.startswith("| **px0**") for line in _read("framework/39-connectors-setup.md").splitlines())


def test_build_runs_px0_per_pr_and_cleans_up():
    build = _read(BUILD)
    assert "px0 -no-open -no-telemetry -no-update -port 0" in build and "<pr-url>" in build
    assert "kill -INT" in build
    assert "git worktree prune" in build
    assert "never goes on a Notion page" in build


def test_combined_pr_is_a_labelled_draft_never_merged():
    build = _read(BUILD)
    assert "--draft" in build and "--label Need_Preview_Env" in build
    assert "never merged" in build
    assert "gh pr view <n> --json labels,isDraft" in build


def test_sub_agent_guards_doc_is_listed_and_wired():
    doc = _read("framework/51-sub-agents.md")
    assert "./51-sub-agents.md" in _read("framework/index.md")
    assert "Depth at most 2" in doc
    assert "`Sub-agent depth: <n> of 2.`" in doc
    assert "council_budget" in doc and "platform concurrency" in doc and "hard stop" in doc
    assert "One retry" in doc
    assert "cross-family review CLI" in doc and "leaf" in doc
    assert "claude -p" in doc and "codex exec" in doc and "count as sub-agents" in doc
    for rel in ("skills/harness-council/SKILL.md", "skills/artifact-audit/SKILL.md", "skills/harness-intake/SKILL.md"):
        text = _read(rel)
        assert "51-sub-agents.md" in text or "doc 51" in text, rel


def test_no_harness_agent_can_spawn_agents():
    for path in (PLUGIN / "agents").glob("*.md"):
        tools = _frontmatter_tools(path.read_text())
        names = _tool_names(tools)
        assert not names & {"Agent", "Task"}, path.name


def test_agent_tools_allowlist_accepts_yaml_forms_and_checks_quoted_names():
    assert _tool_names(["Read", "Grep"]) == {"Read", "Grep"}
    assert _tool_names("Read, Grep") == {"Read", "Grep"}
    assert _tool_names(_frontmatter_tools('---\nname: probe\ntools: "Read, Agent"\n---\n')) & {"Agent", "Task"}
    assert _tool_names(_frontmatter_tools('---\nname: probe\ntools: [Read, Task]\n---\n')) & {"Agent", "Task"}
    assert _tool_names(_frontmatter_tools('---\nname: probe\ntools:\n  - Read\n  - Agent\n---\n')) & {"Agent", "Task"}


def test_harness_profile_template_substitutes_to_valid_nested_yaml():
    rendered = re.sub(r"{{.*?}}", "sample", _read("framework/templates/harness-profile.yml"))
    profile = yaml.safe_load(rendered)
    assert profile["initiatives"] == ["sample"]
    assert profile["default_run"] == "sample-run1"
    assert profile["connectors"]["notion"] == "present"
    assert profile["tools"]["claude_code"] == "present"
    assert profile["models"]["routes_available"] == ["anthropic", "openai"]
    assert profile["focus"]["gate_owned"] == "sample"


def test_px0_and_preview_pr_commands_execute_with_stubs(tmp_path):
    build = _read(BUILD)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls"
    stub = bin_dir / "stub"
    stub.write_text('#!/bin/sh\nprintf "%s\\n" "$0 $*" >> "$HARNESS_CALLS"\n')
    stub.chmod(0o755)
    (bin_dir / "px0").symlink_to(stub)
    (bin_dir / "gh").symlink_to(stub)
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}", "HARNESS_CALLS": str(calls)}

    px0_line = next(line.strip() for line in build.splitlines() if line.strip().startswith("nohup px0 "))
    px0_command = px0_line.removeprefix("nohup ").split(" > ", 1)[0].replace("<pr-url>", "https://example.test/pull/7")
    subprocess.run(px0_command, shell=True, check=True, env=env)

    command_match = re.search(r"(?m)^\s*gh pr create --draft --label Need_Preview_Env", build)
    assert command_match, "combined preview PR creation must be an executable command, not a comment"
    command_lines = build[command_match.start():].split("```", 1)[0].splitlines()
    gh_command = " ".join(line.strip().rstrip("\\").strip() for line in command_lines)
    replacements = {"<default-branch>": "main", "<feature-branch>": "topic", "<feature>": "Feature", "<body>": "body.md"}
    for old, new in replacements.items():
        gh_command = gh_command.replace(old, new)
    subprocess.run(gh_command, shell=True, check=True, env=env)

    recorded = calls.read_text()
    assert "px0 -no-open -no-telemetry -no-update -port 0 -y https://example.test/pull/7" in recorded
    assert "gh pr create --draft --label Need_Preview_Env --base main --head topic-combined" in recorded
    assert "--body-file body.md" in recorded


def test_px0_version_parser_accepts_prefixed_and_unprefixed_output(tmp_path):
    onboard = _read("skills/harness-onboard/SKILL.md")
    assignment = next(line for line in onboard.splitlines() if line.startswith("PX0_REPORTED_VERSION=$(px0 -version"))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    px0 = bin_dir / "px0"
    px0.write_text('#!/bin/sh\nprintf "px0 %s (darwin/arm64)\\n" "$HARNESS_PX0_VERSION"\n')
    px0.chmod(0o755)
    for reported in ("1.2.3", "v1.2.3"):
        result = subprocess.run(f'{assignment}; printf "%s" "$PX0_REPORTED_VERSION"', shell=True, check=True,
                                capture_output=True, text=True,
                                env={**os.environ, "HARNESS_PX0_VERSION": reported,
                                     "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"})
        assert result.stdout == "1.2.3"


def test_orchestrator_no_longer_caps_depth_at_3():
    text = _read("agents/product-orchestrator.md")
    assert "Depth cap is 3" not in text
    assert "Sub-agent depth: <n> of 2." in _read("framework/51-sub-agents.md")
    assert "doc 51" in text


def test_px0_is_optional_at_onboarding_and_update_is_verified():
    onboard = _read("skills/harness-onboard/SKILL.md")
    assert "px0 is **optional**" in onboard or "px0 is\n**optional**" in onboard
    assert "`px0 --update`" not in onboard.replace("The in-place `px0 --update`", "")
    assert "brew upgrade px0" in onboard
    assert "bump `px0-pin.yml`" in onboard
    for required in ("engineer →", "QA →", "EM →"):
        line = next(l for l in onboard.splitlines() if required in l)
        assert "px0" not in line, (required, line)
    connectors = _read("framework/39-connectors-setup.md")
    row = next(l for l in connectors.splitlines() if l.startswith("| **px0**"))
    assert "opt-in" in row and "brew upgrade px0" in row


def test_px0_pin_is_shipped_and_defaults_fail_closed():
    import re
    pin = (PLUGIN / "framework/models/px0-pin.yml").read_text()
    assert re.search(r"^version:\s*\"[^\"]+\"", pin, re.M)
    assert re.search(r"^sha256:\s*\"[0-9a-f]{64}\"", pin, re.M)
    onboard = _read("skills/harness-onboard/SKILL.md")
    assert "shasum -a 256 -c -" in onboard
    assert "Refuse to install on a checksum mismatch" in onboard


def test_sub_agents_doc_pins_concurrency_as_hard_stop():
    doc = _read("framework/51-sub-agents.md")
    assert "non-overridable" in doc.lower() or "nobody overrides" in doc
    assert "refused regardless" in doc or "is refused" in doc
    assert "waves" in doc
    assert "no-spawn line" in doc or "Leaf cross-family review. Do not spawn sub-agents." in doc
    assert "exactly one cross-family review" in doc
    for rel in ("skills/harness-council/SKILL.md", "agents/product-orchestrator.md",
                "skills/harness-intake/SKILL.md", "skills/artifact-audit/SKILL.md"):
        text = _read(rel)
        delegates = "framework/51-sub-agents.md" in text and "doc 51 is authoritative" in text
        asserts_locally = "non-overridable" in text or "never overridden" in text or "is the hard stop" in text
        assert delegates or asserts_locally, rel


def test_px0_sections_use_8f_and_8g_not_duplicates():
    build = _read(BUILD)
    headings = [l.strip() for l in build.splitlines() if l.strip().startswith("## 8")]
    assert len(headings) == len(set(headings)), headings
    assert "## 8f. Optional: a px0 review link per PR (added 2026-10-08)" in build
    assert "## 8g. One combined draft PR for manual testing (added 2026-10-08)" in build
    assert "§8e" not in build, "build-stage still has a stale §8e reference"
    for rel in ("README.md", "framework/39-connectors-setup.md",
                "framework/templates/harness-profile.yml",
                "skills/harness-intake/SKILL.md",
                "skills/harness-onboard/SKILL.md",
                "skills/harness-council/SKILL.md"):
        text = _read(rel)
        assert "§8d" not in text and "§8e" not in text, (rel, "stale px0/combined-PR anchor")


def test_orchestrator_depth_rule_is_bulleted_not_a_wall():
    text = _read("agents/product-orchestrator.md")
    marker = "- **Sub-agents follow doc 51**"
    assert marker in text
    start = text.index(marker)
    block = text[start:text.index("\n\n", start)]
    bullets = [l for l in block.splitlines() if l.lstrip().startswith("- ")]
    assert len(bullets) >= 3, block
    assert "concurrency 20" in block and "exactly one cross-family" in block


def test_harness_council_dispatch_step_is_short():
    text = _read("skills/harness-council/SKILL.md")
    import re
    m = re.search(r"\d+\. \*\*Dispatch all lenses.*?(?=\n\d+\.|\n## )", text, re.M | re.S)
    assert m, "dispatch step not found"
    assert len(m.group(0).split()) < 400, len(m.group(0).split())
    assert "framework/51-sub-agents.md" in m.group(0)


def test_px0_offer_is_guarded_against_placeholder_pin():
    onboard = _read("skills/harness-onboard/SKILL.md")
    assert "px0-pin.yml" in onboard
    assert '`"0.0.0"`' in onboard or '"0.0.0"' in onboard
    assert "placeholder" in onboard
    assert "n/a-pending-pin" in onboard
    assert "do not offer the install" in onboard or "do not offer the install at all" in onboard


def test_px0_is_optional_and_never_required_by_scripts():
    build = (PLUGIN / "framework" / "20-build-stage.md").read_text()
    assert "## 8f. Optional: a px0 review link per PR" in build
    assert "optional for every role, including engineers" in build
    for script in (PLUGIN / "scripts").glob("*.py"):
        assert "px0" not in script.read_text(), script.name


def test_install_recipes_point_at_real_branches():
    for path in PLUGIN.rglob("*.md"):
        assert "feat/apollo-product-" not in path.read_text(), path
