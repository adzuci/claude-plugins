#!/usr/bin/env python3
"""Shared rule-registry helpers. The registry is JSON-compatible YAML."""
import json
import os
import re
import tempfile


HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
DEFAULT_REGISTRY = os.path.join(PLUGIN, "framework", "rules", "registry.yml")
RULE_SOURCES = {
    "backend-reviewer": os.path.join(PLUGIN, "agents", "backend-reviewer.md"),
    "frontend-reviewer": os.path.join(PLUGIN, "agents", "frontend-reviewer.md"),
    "db-perf": os.path.join(PLUGIN, "agents", "db-perf.md"),
    "security-reviewer": os.path.join(PLUGIN, "agents", "security-reviewer.md"),
    "infra-lens": os.path.join(PLUGIN, "framework", "apollo-infra-patterns.md"),
    "supervisor-hygiene": os.path.join(PLUGIN, "skills", "code-review", "SKILL.md"),
}
PREFIXES = {
    "backend-reviewer": ("B",),
    "frontend-reviewer": ("F",),
    "db-perf": ("M",),
    "security-reviewer": ("S",),
    "infra-lens": ("IP",),
    "supervisor-hygiene": ("H",),
}
STATUSES = {"candidate", "shadow", "active", "retired"}


def load_registry(path=DEFAULT_REGISTRY):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        raise ValueError("registry must contain a rules list")
    indexed = {}
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("id"), str):
            raise ValueError("every registry rule must have a string id")
        if rule["id"] in indexed:
            raise ValueError("duplicate registry rule %s" % rule["id"])
        if rule.get("status") not in STATUSES:
            raise ValueError("registry rule %s has an invalid status" % rule["id"])
        indexed[rule["id"]] = rule
    return data, indexed


def write_registry(path, data):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".registry-", suffix=".yml", dir=directory, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def finding_rule_ids(finding):
    if not isinstance(finding, dict):
        return []
    raw = finding.get("rule") or finding.get("rule_id") or []
    raw = raw if isinstance(raw, list) else [raw]
    ids = []
    for value in raw:
        ids.extend(token.upper() for token in re.split(r"[/,;\s]+", str(value or "")) if token)
    return ids


def definition_lines(path):
    agent = next(name for name, source in RULE_SOURCES.items() if source == path)
    prefixes = PREFIXES[agent]
    definitions = {}
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    patterns = [
        re.compile(r"^\s*-\s+\**(?P<id>[A-Z]{1,2}\d+)\b"),
        re.compile(r"^\s*##\s+(?P<id>IP\d+)\b"),
        re.compile(r"^\s*\|\s*(?P<id>IP\d+)\s*\|"),
    ]
    for line in lines:
        if agent == "supervisor-hygiene":
            match = re.search(r"\brule `?(?P<id>H\d+)`?", line)
            if match:
                definitions.setdefault(match.group("id"), line)
                continue
        for pattern in patterns:
            match = pattern.match(line)
            if match and any(match.group("id").startswith(prefix) for prefix in prefixes):
                definitions.setdefault(match.group("id"), line)
                break
    return definitions


def prompt_rules():
    found = {}
    for agent, path in RULE_SOURCES.items():
        for rule_id, text in definition_lines(path).items():
            found[rule_id] = {"agent": agent, "path": path, "text": text}
    return found


def remove_rule_bullet(text, rule_id):
    lines = text.splitlines(keepends=True)
    if rule_id.startswith("IP"):
        lines = [line for line in lines if not re.match(r"^\s*\|\s*%s\s*\|" % re.escape(rule_id), line)]
        starts = [i for i, line in enumerate(lines) if re.match(r"^##\s+%s\b" % re.escape(rule_id), line)]
        if len(starts) != 1:
            raise ValueError("expected one section for %s, found %s" % (rule_id, len(starts)))
        start = starts[0]
        end = next((i for i in range(start + 1, len(lines)) if re.match(r"^##\s+IP\d+\b", lines[i])), len(lines))
        return "".join(lines[:start] + lines[end:])
    starts = [i for i, line in enumerate(lines)
              if re.match(r"^\s*-\s+\**%s\b" % re.escape(rule_id), line)
              or re.search(r"\brule `?%s`?" % re.escape(rule_id), line)]
    if len(starts) != 1:
        raise ValueError("expected one bullet for %s, found %s" % (rule_id, len(starts)))
    start = starts[0]
    end = start + 1
    while end < len(lines) and (lines[end].startswith((" ", "\t")) and lines[end].strip()):
        end += 1
    return "".join(lines[:start] + lines[end:])


def rate(numerator, denominator):
    return numerator / denominator if denominator else 0.0
