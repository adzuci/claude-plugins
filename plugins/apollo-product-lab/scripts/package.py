#!/usr/bin/env python3
"""Build the harness for the web surfaces (framework doc 45 §7).

    python3 plugins/apollo-product-lab/scripts/package.py [--out DIR] [--only plugin|skills]

Writes, by default under <repo>/dist/:
  apollo-product-lab.zip   the plugin for claude.ai/code and Desktop (Customize -> Plugins -> Upload):
                           .claude-plugin/plugin.json at the archive root, plus a BUILD file with the commit
  skills/<skill>.zip       claude.ai chat Skills (Settings -> Capabilities -> Skills -> Upload): one folder
                           per skill with SKILL.md, the framework docs, agent briefs and scripts/storage.py

Only files git tracks or would track (not ignored) are packaged, so no local configuration rides along.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
NAME = os.path.basename(PLUGIN)

# Skills that work without a checkout or an Agent tool (doc 45 §5). The rest need Claude Code.
CHAT_SKILLS = ("harness-onboard", "harness-intake", "harness-snapshot", "harness-council", "artifact-audit",
               "product-harness-init")
CHAT_SCRIPTS = (
    "scripts/storage.py",
    "scripts/post-update.py",
    "scripts/grill-check.py",
    "scripts/verify-claims.py",
)
CHAT_EXCLUDE = ("framework/eval/", "framework/reviews/", "framework/scripts/")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CHAT_NOTE = (
    "> Packaged for claude.ai chat (doc 45). Paths that started with the plugin root are relative to this\n"
    "> skill's folder. There is no repo, no Agent tool and no hook here: storage is `notion` (doc 45 §2),\n"
    "> lenses run in this thread and the memo says `degraded: in-thread lenses` (doc 45 §5).\n"
)


def git(*args) -> str:
    r = subprocess.run(["git", "-C", PLUGIN, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def plugin_files() -> list:
    listed = git("ls-files", "--cached", "--others", "--exclude-standard", "--full-name", ".")
    prefix = git("rev-parse", "--show-prefix")
    if not listed:
        # Fail closed: without git's ignore rules a walk would package developer-local configuration.
        raise ValueError("cannot list the plugin's files with git; build from a git checkout")
    files = [p[len(prefix):] if prefix and p.startswith(prefix) else p for p in listed.splitlines()]
    real_plugin = os.path.realpath(PLUGIN)
    keep = []
    for f in files:
        if "__pycache__" in f or f.endswith((".pyc", ".DS_Store")) or f.startswith("dist/"):
            continue
        full = os.path.join(PLUGIN, f)
        if os.path.islink(full) and os.path.commonpath([real_plugin, os.path.realpath(full)]) != real_plugin:
            raise ValueError(f"{f} is a symlink outside the plugin")
        if os.path.isfile(full):
            keep.append(f.replace(os.sep, "/"))
    return sorted(set(keep))


def build_id() -> str:
    sha = git("rev-parse", "--short", "HEAD") or "unknown"
    dirty = git("status", "--porcelain", "--", ".")
    return sha + ("-dirty" if dirty else "")


def frontmatter(text: str) -> tuple:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("SKILL.md has no frontmatter")
    fields = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if k and not k.startswith(" "):
            fields[k.strip()] = v.strip()
    return fields, text[m.end():]


def relative_paths(text: str) -> str:
    text = re.sub(r'"\$\{CLAUDE_PLUGIN_ROOT\}/([^"\s]*)"', r'"\1"', text)
    text = text.replace("${CLAUDE_PLUGIN_ROOT}/", "")
    return text.replace("${CLAUDE_PLUGIN_ROOT}", ".")


def chat_skill_md(text: str) -> str:
    fields, body = frontmatter(text)
    name, desc = fields.get("name", ""), fields.get("description", "")
    if desc.startswith('"'):
        desc = json.loads(desc)
    if not NAME_RE.match(name) or len(name) > 64:
        raise ValueError(f"skill name {name!r} is not valid for claude.ai")
    if "<" in desc or ">" in desc or len(desc) > 1024:
        raise ValueError(f"{name}: description must be at most 1024 characters with no angle brackets")
    desc, body = relative_paths(desc), relative_paths(body)
    # json.dumps gives a double-quoted scalar, which is valid YAML whatever the description contains.
    return f"---\nname: {name}\ndescription: {json.dumps(desc, ensure_ascii=False)}\n---\n\n{CHAT_NOTE}\n{body.lstrip()}"


def add_file(z, src: str, arc: str) -> None:
    path = os.path.join(PLUGIN, src)
    if src.endswith((".md", ".yml", ".yaml", ".json", ".py", ".sh", ".toml", ".example")):
        with open(path, encoding="utf-8") as fh:
            z.writestr(arc, relative_paths(fh.read()))
    else:
        z.write(path, arc)


def build_plugin(out: str, files: list) -> str:
    dest = os.path.join(out, f"{NAME}.zip")
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(PLUGIN, f), f)
        z.writestr("BUILD", build_id() + "\n")
    return dest


def build_skills(out: str, files: list) -> list:
    os.makedirs(os.path.join(out, "skills"), exist_ok=True)
    # Skills cross-reference each other's SKILL.md, templates and references by plugin-root path, so the
    # whole skills tree (minus evals and scripts) ships inside every chat Skill.
    shared = [f for f in files if (f.startswith(("framework/", "agents/", "skills/")) or f in CHAT_SCRIPTS)
              and not f.startswith(CHAT_EXCLUDE) and "/eval/" not in f and "/scripts/" not in f]
    built = []
    for skill in CHAT_SKILLS:
        src = f"skills/{skill}/"
        own = [f for f in files if f.startswith(src)]
        if f"{src}SKILL.md" not in own:
            raise ValueError(f"missing {src}SKILL.md")
        dest = os.path.join(out, "skills", f"{skill}.zip")
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
            for f in own:
                rel = f[len(src):]
                if rel == "SKILL.md":
                    with open(os.path.join(PLUGIN, f), encoding="utf-8") as fh:
                        z.writestr(f"{skill}/SKILL.md", chat_skill_md(fh.read()))
                else:
                    add_file(z, f, f"{skill}/{rel}")
            for f in shared:
                add_file(z, f, f"{skill}/{f}")
            z.writestr(f"{skill}/BUILD", build_id() + "\n")
        built.append(dest)
    return built


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    repo = git("rev-parse", "--show-toplevel") or os.path.dirname(os.path.dirname(PLUGIN))
    p.add_argument("--out", default=os.path.join(repo, "dist"))
    p.add_argument("--only", choices=("plugin", "skills"))
    a = p.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    try:
        files = plugin_files()
    except ValueError as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 1
    if ".claude-plugin/plugin.json" not in files:
        print("refusing: .claude-plugin/plugin.json is not in the package list", file=sys.stderr)
        return 1
    try:
        if a.only != "skills":
            print(build_plugin(a.out, files))
        if a.only != "plugin":
            for path in build_skills(a.out, files):
                print(path)
    except ValueError as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
