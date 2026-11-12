#!/usr/bin/env python3
"""Install the house-manager agent: managed /hm skill, helper scripts, vault note.

Dry-run by default; pass --apply to write. Re-running is idempotent. Nothing
here touches settings.json, hooks, launchd, or any secret.

Subcommands:
  check      read-only environment report (JSON)
  install    install managed copies and write config/vault note
  uninstall  remove only what install created (marker-guarded)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

MARKER = ".house-managed.json"
CLIENT_DIRS = {"claude": Path(".claude/skills"), "codex": Path(".codex/skills")}
HELPERS = ("nest_auth.py", "notify.py")
DEFAULT_SCHEDULE = "0 18 * * 0"  # Sunday 18:00 local
E164 = re.compile(r"^\+[1-9]\d{6,14}$")

SKILLS_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent


def home() -> Path:
    return Path(os.environ.get("HOME") or Path.home())


def config_dir() -> Path:
    return home() / ".config" / "adzuci-house"


def detect_clients(which: Callable[[str], Optional[str]] = shutil.which) -> List[str]:
    return [client for client in CLIENT_DIRS if which(client)]


def codex_text(text: str) -> str:
    return re.sub(r"^disable-model-invocation:\s*true\s*\n", "", text, flags=re.MULTILINE)


def check(vault: Optional[str], which: Callable[[str], Optional[str]] = shutil.which) -> Dict[str, Any]:
    vault_path = Path(vault).expanduser() if vault else None
    config = config_dir() / "config.json"
    return {
        "macos": sys.platform == "darwin",
        "python": sys.version.split()[0],
        "claude": bool(which("claude")),
        "codex": bool(which("codex")),
        "twilio_cli": bool(which("twilio")),
        "gcloud": bool(which("gcloud")),
        "security_keychain": bool(which("security")),
        "vault": str(vault_path) if vault_path else None,
        "vault_exists": bool(vault_path and vault_path.is_dir()),
        "vault_has_agents_dir": bool(vault_path and (vault_path / "agents").is_dir()),
        "config_exists": config.is_file(),
        "hm_installed": {c: (home() / d / "hm" / MARKER).is_file() for c, d in CLIENT_DIRS.items()},
    }


def agent_note() -> str:
    return """---
type: agent
name: house-manager
audience: me (household admin)
reads_vault: true
skill_path: ~/.claude/skills/hm/SKILL.md
status: active
---

# Agent: house-manager

## Job Brief

Weekly review of household email, calendar, and (optionally) Nest thermostats.
Writes a digest into `house/digests/` and adds concrete to-dos to the backlog.

## Audience / Owner

Me. Maintained by the `house` plugin (`/house:house-setup`).

## Inputs

None. Run `/hm`, or let the weekly scheduled job run it.

## Tools & Skills

- Gmail connector (read-only: search and read threads)
- Google Calendar connector (read-only: list/search events)
- Google Drive connector (optional, read-only)
- Nest status helper (`~/.config/adzuci-house/bin/nest_auth.py status`)
- Twilio alert helper (`notify.py`), urgent items only, dry-run unless sent
- `/productivity:todo` for backlog tasks (optional)

## Reads Vault?

Yes. Start at `index.md`. May write only under `house/`.

## Workflow

1. Read `house/README.md` and the latest digest for context.
2. Search the last 7 days of email for bills, renewals, contractors, deliveries, HOA and recalls.
3. List the next 14 days of calendar events that involve the house.
4. If Nest is configured, run the status helper and note any flags.
5. Write `house/digests/<date>.md`; add backlog tasks; alert only for urgent items.

## Guardrails

- Never send, reply to, forward, label, trash, or delete email. Read and search only.
- Never create or change calendar events without an explicit request.
- Alerts only for the urgent rules in `house/README.md`; respect quiet hours.
- No secrets, account numbers, or full card/phone numbers in the vault.

## Linked Skill

`~/.claude/skills/hm/SKILL.md` (managed copy of the `house` plugin's `hm` skill).
"""


def house_readme() -> str:
    return """# House

Notes for the house-manager agent (`/hm`).

- `digests/` - one weekly digest per run (`YYYY-MM-DD.md`).
- Urgent rules (edit freely): past-due bill, service outage, freeze risk (<50F), device offline over 24h.
- Never store account numbers or secrets here.
"""


def plan(vault: Optional[Path], clients: List[str], notify_to: Optional[str]) -> List[str]:
    actions = [
        f"copy helper scripts to {config_dir() / 'bin'}",
        f"write config {config_dir() / 'config.json'} (mode 600, no secrets)",
    ]
    for client in clients:
        actions.append(f"install managed /hm skill to {home() / CLIENT_DIRS[client] / 'hm'}")
    if vault:
        actions.append(f"create {vault / 'agents' / 'house-manager.md'} (if absent)")
        actions.append(f"create {vault / 'house' / 'README.md'} and house/digests/ (if absent)")
    if notify_to:
        actions.append("record the alert phone number in config (E.164, not a secret)")
    return actions


def install(
    vault: Optional[str],
    clients: List[str],
    apply: bool,
    notify_to: Optional[str] = None,
    twilio_from: Optional[str] = None,
    twilio_profile: Optional[str] = None,
) -> Dict[str, Any]:
    vault_path = Path(vault).expanduser() if vault else None
    if vault_path and not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist: {vault_path}")
    for number in (notify_to, twilio_from):
        if number and not E164.match(number):
            raise SystemExit("Phone numbers must be E.164, like +19785551234.")
    result: Dict[str, Any] = {"dry_run": not apply, "actions": plan(vault_path, clients, notify_to)}
    if not apply:
        return result

    bin_dir = config_dir() / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    for helper in HELPERS:
        shutil.copy2(SCRIPTS_DIR / helper, bin_dir / helper)
        os.chmod(bin_dir / helper, 0o755)

    cfg_path = config_dir() / "config.json"
    config: Dict[str, Any] = {}
    if cfg_path.is_file():
        config = json.loads(cfg_path.read_text())
    config["bin"] = str(bin_dir)
    config["schedule"] = config.get("schedule", DEFAULT_SCHEDULE)
    if vault_path:
        config["vault"] = str(vault_path)
    if notify_to or twilio_from or twilio_profile:
        notify = config.get("notify", {})
        notify.update({k: v for k, v in (("to", notify_to), ("from", twilio_from), ("profile", twilio_profile)) if v})
        notify.setdefault("quiet_hours", "22-7")
        config["notify"] = notify
    cfg_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    os.chmod(cfg_path, 0o600)

    source = (SKILLS_ROOT / "hm" / "SKILL.md").read_text()
    installed: List[str] = []
    for client in clients:
        target = home() / CLIENT_DIRS[client] / "hm"
        if target.exists() and not (target / MARKER).is_file():
            raise SystemExit(f"Refusing to overwrite unmanaged skill at {target}")
        target.mkdir(parents=True, exist_ok=True)
        text = codex_text(source) if client == "codex" else source
        (target / "SKILL.md").write_text(text)
        (target / MARKER).write_text(json.dumps({"managed_by": "house-setup"}) + "\n")
        installed.append(str(target))
    result["installed_skills"] = installed

    created: List[str] = []
    if vault_path:
        note = vault_path / "agents" / "house-manager.md"
        if (vault_path / "agents").is_dir() and not note.exists():
            note.write_text(agent_note())
            created.append(str(note))
        readme = vault_path / "house" / "README.md"
        if not readme.exists():
            readme.parent.mkdir(parents=True, exist_ok=True)
            readme.write_text(house_readme())
            created.append(str(readme))
        digests = vault_path / "house" / "digests"
        digests.mkdir(parents=True, exist_ok=True)
        keep = digests / ".gitkeep"
        if not keep.exists():
            keep.write_text("keep\n")  # non-empty: empty files misbehave under git-crypt
    result["vault_files_created"] = created
    return result


def uninstall(clients: List[str], apply: bool) -> Dict[str, Any]:
    targets = [home() / CLIENT_DIRS[c] / "hm" for c in clients]
    managed = [t for t in targets if (t / MARKER).is_file()]
    result: Dict[str, Any] = {"dry_run": not apply, "would_remove": [str(t) for t in managed]}
    if apply:
        for target in managed:
            shutil.rmtree(target)
        shutil.rmtree(config_dir() / "bin", ignore_errors=True)
    return result


def main(argv: Optional[List[str]] = None, which: Callable[[str], Optional[str]] = shutil.which) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    chk = sub.add_parser("check")
    chk.add_argument("--vault")

    inst = sub.add_parser("install")
    inst.add_argument("--vault")
    inst.add_argument("--clients", default="auto", help="auto, or comma list of claude,codex")
    inst.add_argument("--notify-to", help="your phone, E.164 (stored in config)")
    inst.add_argument("--twilio-from", help="your Twilio number, E.164")
    inst.add_argument("--twilio-profile", help="twilio CLI profile name")
    inst.add_argument("--apply", action="store_true")

    rm = sub.add_parser("uninstall")
    rm.add_argument("--clients", default="auto")
    rm.add_argument("--apply", action="store_true")

    args = parser.parse_args(argv)

    def resolve(spec: str) -> List[str]:
        if spec == "auto":
            return detect_clients(which) or ["claude"]
        chosen = [c.strip() for c in spec.split(",") if c.strip()]
        bad = [c for c in chosen if c not in CLIENT_DIRS]
        if bad:
            raise SystemExit(f"Unknown client(s): {', '.join(bad)}")
        return chosen

    if args.command == "check":
        print(json.dumps(check(args.vault, which), indent=2))
    elif args.command == "install":
        print(json.dumps(
            install(args.vault, resolve(args.clients), args.apply, args.notify_to, args.twilio_from, args.twilio_profile),
            indent=2,
        ))
    else:
        print(json.dumps(uninstall(resolve(args.clients), args.apply), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
