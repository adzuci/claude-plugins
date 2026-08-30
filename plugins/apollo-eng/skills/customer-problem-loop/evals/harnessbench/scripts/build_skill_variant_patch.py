#!/usr/bin/env python3
"""Build a HarnessBench variant patch that installs a skill into a target repository."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath


def build_patch(skill_dir: Path, target_root: PurePosixPath) -> str:
    if not skill_dir.is_dir():
        raise ValueError(f"skill directory does not exist: {skill_dir}")
    if target_root.is_absolute() or ".." in target_root.parts:
        raise ValueError("target root must be a safe repository-relative path")

    sections: list[str] = []
    for source in sorted(path for path in skill_dir.rglob("*") if path.is_file()):
        relative = PurePosixPath(source.relative_to(skill_dir).as_posix())
        if relative.parts[0] == "evals":
            continue
        target = target_root / relative
        text = source.read_text(encoding="utf-8")
        lines = text.splitlines()
        section = [
            f"diff --git a/{target} b/{target}",
            "new file mode 100644",
            "--- /dev/null",
            f"+++ b/{target}",
            f"@@ -0,0 +1,{len(lines)} @@",
            *(f"+{line}" for line in lines),
        ]
        sections.append("\n".join(section))

    if not sections:
        raise ValueError(f"skill directory contains no files: {skill_dir}")
    return "\n".join(sections) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, required=True)
    parser.add_argument("--target-root", type=PurePosixPath, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    patch = build_patch(args.skill_dir, args.target_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(patch, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
