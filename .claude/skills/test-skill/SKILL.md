---
name: test-skill
description: Test an Apollo marketplace skill, especially skills with Python scripts. Use when asked to add, run, fix, or validate pytest coverage for a skill in apolloio/claude-plugins.
disable-model-invocation: true
---

# Test Skill

Use this workflow in `apolloio/claude-plugins` when a skill has executable code or when a PR changes skill tests.

## Workflow

1. Identify the target skill path:

   ```text
   plugins/<plugin-name>/skills/<skill-name>/
   ```

1. If the skill has no `scripts/` directory and no existing `tests/`, say that pytest coverage is optional unless the change adds meaningful logic.

1. For Python scripts, keep helpers importable:

   - Put pure logic at module scope.
   - Put `print`, `sys.exit`, and `argparse` behind `if __name__ == "__main__":`.
   - Add `from __future__ import annotations` when scripts use `X | Y` union types and must run on Python 3.9.

1. Add tests beside the skill:

   ```text
   plugins/<plugin>/skills/<skill>/
   ├── scripts/
   └── tests/
       ├── conftest.py
       ├── requirements.txt
       └── test_<module>.py
   ```

   `tests/conftest.py` should add `../scripts` to `sys.path`. Use `pytest.importorskip("<module>")` when a script may land in a separate PR.

1. Install test dependencies:

   ```bash
   pip install -r tests/requirements.txt
   pip install -r plugins/<plugin>/skills/<skill>/tests/requirements.txt
   ```

   Skip the second command when the skill has no test requirements file.

1. Run the targeted tests first:

   ```bash
   python -m pytest plugins/<plugin>/skills/<skill>/tests -q
   ```

1. Run marketplace validation tests before push:

   ```bash
   python -m pytest tests/test_marketplace.py -q
   ```

1. If the skill genuinely needs Python 3.10+ syntax such as `match`, add a module-level version skip in the test file.

## Review Checklist

- Tests exercise meaningful script behavior, not only imports.
- Test dependencies are declared in the nearest `tests/requirements.txt`.
- Scripts import cleanly without running CLI side effects.
- Targeted skill tests and marketplace tests pass or the blocker is documented.
