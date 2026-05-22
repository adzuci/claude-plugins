import pytest

analyze_context = pytest.importorskip("analyze_context")


class TestParseContextOutput:
    def test_parses_basic_context_output(self):
        raw = """Context window: 45% (90k / 200k tokens)

Top contributors:
  CLAUDE.md: 12%
  src/components/Button.tsx: 8%
  package.json: 3%
"""
        result = analyze_context.parse_context_output(raw)
        assert result["pct"] == 45
        assert len(result["contributors"]) == 3
        assert result["contributors"][0] == {"name": "CLAUDE.md", "pct": 12}

    def test_parses_bullet_format(self):
        raw = """Context: 30%

- node_modules/lodash/index.js: 15%
- src/index.ts: 5%
"""
        result = analyze_context.parse_context_output(raw)
        assert result["pct"] == 30
        assert len(result["contributors"]) == 2
        assert result["contributors"][0]["name"] == "node_modules/lodash/index.js"
        assert result["contributors"][0]["pct"] == 15

    def test_handles_decimal_percentages(self):
        raw = """Context window: 12.5%
  file.ts: 3.5%
"""
        result = analyze_context.parse_context_output(raw)
        assert result["pct"] == 12.5
        assert result["contributors"][0]["pct"] == 3.5

    def test_handles_empty_output(self):
        result = analyze_context.parse_context_output("")
        assert result["pct"] is None
        assert result["contributors"] == []


class TestAnalyzeContributors:
    def test_detects_node_modules(self):
        contributors = [{"name": "node_modules/lodash/index.js", "pct": 10}]
        issues, _ = analyze_context.analyze_contributors(contributors)
        assert len(issues) == 1
        assert "node_modules" in issues[0]["reason"]

    def test_detects_lockfiles(self):
        contributors = [
            {"name": "package-lock.json", "pct": 8},
            {"name": "yarn.lock", "pct": 5},
        ]
        issues, _ = analyze_context.analyze_contributors(contributors)
        assert len(issues) == 2
        assert any("package-lock.json" in i["reason"] for i in issues)
        assert any("yarn.lock" in i["reason"] for i in issues)

    def test_detects_build_artifacts(self):
        contributors = [
            {"name": "dist/bundle.js", "pct": 4},
            {"name": "build/output.js", "pct": 3},
            {"name": ".next/cache/webpack", "pct": 6},
        ]
        issues, _ = analyze_context.analyze_contributors(contributors)
        assert len(issues) == 3

    def test_flags_high_pct_items(self):
        contributors = [
            {"name": "CLAUDE.md", "pct": 12},
            {"name": "src/index.ts", "pct": 2},
        ]
        _, high_pct = analyze_context.analyze_contributors(contributors)
        assert len(high_pct) == 1
        assert high_pct[0]["name"] == "CLAUDE.md"
        assert high_pct[0]["pct"] == 12

    def test_clean_contributors_no_issues(self):
        contributors = [
            {"name": "src/index.ts", "pct": 3},
            {"name": "CLAUDE.md", "pct": 2},
        ]
        issues, high_pct = analyze_context.analyze_contributors(contributors)
        assert len(issues) == 0
        assert len(high_pct) == 0


class TestGenerateFix:
    def test_generates_combined_fix(self):
        issues = [
            {"name": "node_modules/x", "fix": "Add to .claudeignore: node_modules/"},
            {"name": "dist/y", "fix": "Add to .claudeignore: dist/"},
        ]
        fix = analyze_context.generate_fix(issues)
        assert "Add to .claudeignore:" in fix
        assert "node_modules/" in fix
        assert "dist/" in fix

    def test_deduplicates_patterns(self):
        issues = [
            {"name": "node_modules/a", "fix": "Add to .claudeignore: node_modules/"},
            {"name": "node_modules/b", "fix": "Add to .claudeignore: node_modules/"},
        ]
        fix = analyze_context.generate_fix(issues)
        assert fix.count("node_modules/") == 1

    def test_returns_none_for_empty_issues(self):
        assert analyze_context.generate_fix([]) is None


class TestSuggestIgnorePattern:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("node_modules/lodash/index.js", "node_modules/"),
            ("dist/bundle.js", "dist/"),
            ("build/output.js", "build/"),
            ("package-lock.json", "package-lock.json"),
            ("src/file.min.js", "*.min.js"),
        ],
    )
    def test_suggests_correct_pattern(self, name, expected):
        pattern = analyze_context._suggest_ignore_pattern(name)
        assert pattern == expected


class TestFullAnalysis:
    def test_baseline_ok_no_issues(self):
        context_data = {
            "pct": 10,
            "contributors": [{"name": "CLAUDE.md", "pct": 3}],
        }
        issues, _ = analyze_context.analyze_contributors(context_data["contributors"])
        baseline_ok = context_data["pct"] <= analyze_context.BASELINE_THRESHOLD_PCT
        assert baseline_ok is True
        assert len(issues) == 0

    def test_baseline_too_high(self):
        context_data = {"pct": 25, "contributors": []}
        baseline_ok = context_data["pct"] <= analyze_context.BASELINE_THRESHOLD_PCT
        assert baseline_ok is False

    def test_score_1_when_clean(self):
        context_data = {
            "pct": 10,
            "contributors": [{"name": "src/index.ts", "pct": 2}],
        }
        issues, _ = analyze_context.analyze_contributors(context_data["contributors"])
        baseline_ok = context_data["pct"] <= analyze_context.BASELINE_THRESHOLD_PCT
        score = 1 if (baseline_ok and len(issues) == 0) else 0
        assert score == 1

    def test_score_0_when_issues(self):
        context_data = {
            "pct": 10,
            "contributors": [{"name": "node_modules/x", "pct": 5}],
        }
        issues, _ = analyze_context.analyze_contributors(context_data["contributors"])
        baseline_ok = context_data["pct"] <= analyze_context.BASELINE_THRESHOLD_PCT
        score = 1 if (baseline_ok and len(issues) == 0) else 0
        assert score == 0
