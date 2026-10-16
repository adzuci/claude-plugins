#!/usr/bin/env python3
"""Storage for the harness record: local files or Notion pages (framework doc 45).

The files under .ai/<initiative>/ are the canonical schema on every host. In notion mode each file is
one "record page" whose body carries the file byte for byte (base64), so Notion <-> local sync is lossless.
This script never calls Notion itself: it prints the Notion tool calls to make (to-notion) and turns a
fetched page back into the file (from-notion). The session executes the calls with the Notion MCP.

    storage.py detect [--surface terminal|desktop-code|claude-code-cloud|claude-ai-chat] [--profile P]
    storage.py to-notion PATH --initiative SLUG [--parent-id ID]      PATH is a file or a directory under .ai/SLUG/
    storage.py profile-to-notion PROFILE.yml --name NAME             private draft page, no parent
    storage.py from-notion FETCHED.md [--root DIR] [--initiative SLUG] [--stdout] [--replace] [--unverified]
    storage.py ledger-entry LEDGER_PAGE.md [--unverified] -- APPEND_ARGS...   validate one event against the ledger page

Exit codes: 0 ok; 1 usage, validation or safety refusal; 3 record hash mismatch (the page was edited by hand).
Record pages use format harness-record/2: the exact file bytes as base64 with their sha256, so a round
trip is byte for byte. Pages hand-built without code execution are plain text and import only with
--unverified.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import errno
import hashlib
import html
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unicodedata
import urllib.parse

try:
    import fcntl
except ImportError:  # not POSIX: the append-only check still runs, without the lock
    fcntl = None

try:
    import yaml
except ImportError:  # the raw-text scan still runs without PyYAML
    yaml = None

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
APPEND = os.path.join(PLUGIN, "framework", "ledger", "append.py")

SURFACES = ("terminal", "desktop-code", "claude-code-cloud", "claude-ai-chat")
HEADER = "Machine record of the apollo-product-lab. Do not edit by hand; a new version supersedes it."
# A code fence inside a record would end the Notion code block early. The escape puts a zero-width
# space after the first backtick; from-notion removes exactly that sequence.
FENCE = "```"
ESCAPED_FENCE = "`​``"
LEDGER_KEY = "ledger.jsonl"

SKIPS = {
    "terminal": [],
    "desktop-code": ["fabric-studio previews (observed broken in the Desktop Code tab; use the CLI)"],
    "claude-code-cloud": [
        "shunt and the Codex plugin (laptop processes; the adversary falls back per doc 35)",
        "fabric-studio previews and in-studio comments (VPN)",
        "playwright against preview environments (VPN)",
        "docker / rails container",
    ],
    "claude-ai-chat": [
        "shunt and the Codex plugin",
        "fabric-studio previews",
        "playwright, docker, git, gh, record-sync.sh",
        "parallel lens dispatch (no Agent tool): lenses run in-thread, tagged degraded",
        "design-diff inventory and the agent files product-harness-init would write (need a checkout)",
    ],
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def profile_field(path: str, key: str) -> str:
    try:
        with open(path) as f:
            for line in f:
                m = re.match(rf"^{re.escape(key)}:\s*([^#\s]+)", line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return ""


def profile_updates(path: str) -> dict:
    updates = {}
    try:
        with open(path) as f:
            in_updates = False
            indent = 0
            for raw in f:
                if re.match(r"^updates:\s*(?:#.*)?$", raw):
                    in_updates = True
                    indent = len(raw) - len(raw.lstrip())
                    continue
                if not in_updates:
                    continue
                if raw.strip() and len(raw) - len(raw.lstrip()) <= indent:
                    break
                match = re.match(r"^\s+([a-z_]+):\s*([^#\n]*?)\s*(?:#.*)?$", raw)
                if match:
                    updates[match.group(1)] = match.group(2).strip()
    except OSError:
        pass
    return updates


def validate_profile(path: str) -> dict:
    updates = profile_updates(path)
    tracker = updates.get("tracker", "")
    if tracker and tracker not in ("jira", "notion", "both"):
        raise RecordError(
            f"unknown tracker {tracker!r}; expected jira, notion, or both. Next: run /harness-onboard to choose a tracker"
        )
    if tracker in ("jira", "both"):
        project = updates.get("jira_project", "")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", project):
            raise RecordError(
                "updates.jira_project is required for Jira updates. Next: add the Jira project key or rerun /harness-onboard"
            )
    return updates


def can_write(directory: str) -> bool:
    try:
        os.makedirs(directory, exist_ok=True)
        fd, probe = tempfile.mkstemp(prefix=".harness-probe-", dir=directory)
        os.close(fd)
        os.remove(probe)
        return True
    except OSError:
        return False


def repo_root() -> str:
    root = os.environ.get("HARNESS_REPO_ROOT")
    if root:
        return root
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def detect(surface: str | None, profile: str | None, env=None) -> dict:
    env = os.environ if env is None else env
    home = env.get("HOME", "")
    profile = profile or os.path.join(home, ".claude", "harness-profile.yml")
    if os.path.isfile(profile):
        try:
            validate_profile(profile)
        except RecordError as e:
            raise SystemExit(str(e))
    reasons = []
    if not surface:
        surface = env.get("HARNESS_SURFACE") or ""
    if not surface:
        if env.get("CLAUDE_CODE_REMOTE", "").lower() in ("1", "true"):
            surface = "claude-code-cloud"
            reasons.append("CLAUDE_CODE_REMOTE is set: cloud sandbox, home directory is not kept")
        else:
            surface = "terminal"
            reasons.append("no cloud marker: local Claude Code (terminal or Desktop Code tab)")
    if surface not in SURFACES:
        raise SystemExit(f"unknown surface {surface!r}; one of {', '.join(SURFACES)}")

    home_writable = bool(home) and can_write(os.path.join(home, ".claude"))
    root = repo_root()
    has_ai = bool(root) and os.path.isdir(os.path.join(root, ".ai"))
    override = profile_field(profile, "storage") if os.path.isfile(profile) else ""

    if surface == "claude-ai-chat":
        records, profile_store = "notion", "notion"
        reasons.append("claude.ai chat has no working tree: records and profile live in Notion")
    elif surface == "claude-code-cloud":
        profile_store = "notion"
        records = "notion"
        if override == "local" and has_ai and can_write(os.path.join(root, ".ai")):
            records = "local"
            reasons.append("profile says storage: local and the cloned repo has a writable .ai/: records commit on the branch")
        elif override == "local":
            reasons.append("profile says storage: local but the repo has no .ai/: using notion")
        else:
            reasons.append("cloud session: records default to notion so they outlive the sandbox")
    else:
        profile_store = "local" if home_writable else "notion"
        if not home_writable:
            reasons.append("cannot write ~/.claude: profile lives in Notion")
        records = override if override in ("local", "notion") else ("local" if root else "notion")
        if not root and not override:
            reasons.append("not in a git repo (no-repo mode): records go to Notion instead of being skipped")
        if records == "local" and not root:
            records = "notion"
            reasons.append("storage: local needs a git repo to hold .ai/: using notion")
        if records == "local" and not can_write(os.path.join(root, ".ai") if has_ai else root):
            records = "notion"
            reasons.append("the repo's .ai/ is not writable: using notion")
        if override:
            reasons.append(f"profile override storage: {override}")
    return {
        "surface": surface,
        "storage": records,
        "profile_store": profile_store,
        "repo_root": root or None,
        "repo_has_ai": has_ai,
        "home_writable": home_writable,
        "skip": SKIPS[surface],
        "reasons": reasons,
        "say": f"storage: {records} (surface {surface}; profile in {profile_store})",
    }


KEY_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PROFILE_KEY = "harness-profile.yml"
UNVERIFIED_KEY = "unverified-imports.jsonl"
# A path start is not glued to a word, URL or hash-route character (https://x.com/Users/1, #/home/x and
# src//home/x pass); http(s) URLs are masked before matching, so a path inside one is a link, not a leak.
_START = r"(?<![\w.#~-])(?<![\w.-]/)"
LOCAL_PATH_PATTERNS = [
    _START + r"/(?:Users|home)/[^/\s\"'`<>|]",
    _START + r"/(?:root|Volumes|private|tmp|var/folders|var/tmp|var/root)(?![\w.-])",
    _START + r"/mnt/[a-z](?:/|(?![\w.-]))",
    r"(?<![\w])[A-Za-z]:[\\/]",
    r"(?<![\w\\])\\\\[\w.$-]+\\",
    r"(?<![\w:/])//[\w$-]+/[\w.$-]",
    _START + r"~(?:[A-Za-z][\w.-]*)?[/\\]",
    r"%(?:USERPROFILE|HOMEPATH|HOMEDRIVE|HOMESHARE|APPDATA|LOCALAPPDATA|TEMP|TMP|ONEDRIVE)%",
    r"\$(?:\{\s*)?(?:HOME|TMPDIR|USERPROFILE|XDG_[A-Z_]+_HOME)(?![\w])",
    r"\$env:(?:USERPROFILE|HOMEPATH|HOMEDRIVE|APPDATA|LOCALAPPDATA|TEMP|TMP|HOME)(?![\w])",
    r"file:/",
]
LOCAL_PATH = re.compile("|".join(f"(?:{p})" for p in LOCAL_PATH_PATTERNS), re.I)
URL = re.compile(r"\bhttps?://[^\s<>\"'`)\]|]+", re.I)
B64_WIDTH = 76


class RecordError(ValueError):
    pass


class HashMismatch(RecordError):
    pass


def check_key(key: str) -> str:
    parts = key.split("/")
    if key.startswith("/") or not all(KEY_PART.match(p) for p in parts) or any(p in (".", "..") for p in parts):
        raise RecordError(f"unsafe record_key {key!r}: relative path of plain names only")
    return key


def check_slug(initiative: str) -> str:
    if not SLUG.match(initiative or ""):
        raise RecordError(f"unsafe initiative slug {initiative!r}")
    return initiative


_ESCAPES = [
    (re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}"), lambda m: _chr(m.group(1))),
    (re.compile(r"\\U([0-9a-fA-F]{8})"), lambda m: _chr(m.group(1))),
    (re.compile(r"\\u([0-9a-fA-F]{4})"), lambda m: _chr(m.group(1))),
    (re.compile(r"\\x([0-9a-fA-F]{2})"), lambda m: _chr(m.group(1))),
    (re.compile(r"\\([0-7]{3})"), lambda m: _chr(m.group(1), 8)),
    (re.compile(r"\\/"), lambda m: "/"),
    (re.compile(r"\\\\"), lambda m: "\\"),
]
FENCED = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\n]*\n(.*?)^ {0,3}\1", re.S | re.M)
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n(?:---|\.\.\.)\s*$", re.S | re.M)
BASE64_RUN = re.compile(r"[A-Za-z0-9+/_-]{16,}={0,2}")
MAX_SCANNED_TEXTS = 20_000
MAX_DECODE_PASSES = 32
MAX_NESTING = 6


class _Unscannable(Exception):
    pass


def _chr(digits: str, base: int = 16) -> str:
    try:
        return chr(int(digits, base))
    except (ValueError, OverflowError):
        return ""


def _unescape_once(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    text = html.unescape(urllib.parse.unquote(text))
    for pattern, repl in _ESCAPES:
        text = pattern.sub(repl, text)
    return text


def _variants(text: str) -> list:
    """The text and each successive decoding of it (unicode/url/html/backslash escapes) until it stops
    changing. Every pass is kept: collapsing a doubled backslash twice would hide a UNC prefix."""
    seen = [text]
    for _ in range(MAX_DECODE_PASSES):
        text = _unescape_once(text)
        if text == seen[-1]:
            return seen
        seen.append(text)
    raise _Unscannable("more nested encodings than the publish check decodes")


def _decodings(data: bytes) -> list:
    out = [data.decode("utf-8", errors="replace")]
    if b"\x00" in data:
        out += [data.decode(enc, errors="replace") for enc in ("utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")]
        out.append(data.replace(b"\x00", b"").decode("utf-8", errors="replace"))
    return out


def _yaml_strings(chunk: str) -> list:
    """Every scalar in the YAML node graph (keys, values, any tag; !!binary decoded). Composing, not
    constructing, so unknown tags and aliases cannot stop the walk. Raises on depth trouble."""
    out, seen = [], set()
    try:
        roots = list(yaml.compose_all(chunk, Loader=yaml.SafeLoader))
    except RecursionError:
        raise _Unscannable("YAML nested too deep")
    except yaml.YAMLError:
        return out
    stack = [n for n in roots if n is not None]
    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        if isinstance(node, yaml.ScalarNode):
            out.append(str(node.value))
            if node.tag.endswith(":binary"):
                try:
                    out.extend(_decodings(base64.b64decode("".join(str(node.value).split()))))
                except (ValueError, binascii.Error):
                    pass
        elif isinstance(node, yaml.SequenceNode):
            stack.extend(node.value)
        elif isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                stack.extend((k, v))
    return out


def _json_strings(chunk: str) -> list:
    try:
        obj = json.loads(chunk)
    except RecursionError:
        raise _Unscannable("JSON nested too deep")
    except ValueError:
        return []
    out, stack = [], [obj]
    while stack:
        o = stack.pop()
        if isinstance(o, str):
            out.append(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                stack.extend((k, v))
        elif isinstance(o, list):
            stack.extend(o)
    return out


def _inner_texts(text: str) -> list:
    """Strings a reader could get out of text: JSON and YAML scalars (whole text, each line, frontmatter,
    each fenced block) and printable base64 payloads."""
    chunks = [text, *(m.group(2) for m in FENCED.finditer(text))]
    fm = FRONTMATTER.match(text)
    if fm:
        chunks.append(fm.group(1))
    out = []
    for chunk in chunks:
        if chunk.strip():
            out += _json_strings(chunk) + _yaml_strings(chunk)
    for line in text.splitlines():
        if line.strip()[:1] in ("{", "["):
            out += _json_strings(line)
    for run in BASE64_RUN.findall(text):
        for decode in (base64.b64decode, base64.urlsafe_b64decode):
            try:
                raw = decode(run + "=" * (-len(run) % 4)).decode("utf-8")
            except (ValueError, binascii.Error, UnicodeDecodeError):
                continue
            if raw.isprintable() or all(c.isprintable() or c in "\n\r\t" for c in raw):
                out.append(raw)
    return [t for t in out if t != text]


def find_local_path(content) -> str | None:
    """The first laptop path in content (bytes or text), in any decoded form; None when there is none.
    Anything too deep, too nested or too large to finish scanning counts as a finding: it rejects on doubt."""
    if yaml is None:
        return "<unscannable: PyYAML is required for the publish check (pip install pyyaml)>"
    queue = [(t, 0) for t in (_decodings(content) if isinstance(content, bytes) else [content])]
    seen = set()
    try:
        while queue:
            text, depth = queue.pop()
            if depth > MAX_NESTING:
                raise _Unscannable("more nested content than the publish check scans")
            for variant in _variants(text):
                if variant in seen:
                    continue
                seen.add(variant)
                if len(seen) > MAX_SCANNED_TEXTS:
                    raise _Unscannable("more content than the publish check scans")
                masked = URL.sub(" ", variant)
                m = LOCAL_PATH.search(masked)
                if m:
                    return masked[m.start():m.start() + 40]
                if re.search(r"file:/", variant, re.I):
                    return "file:/"
                queue.extend((t, depth + 1) for t in _inner_texts(variant))
    except (_Unscannable, RecursionError) as e:
        return f"<unscannable: {e or 'nested too deep'}>"
    return None


def check_publishable(key: str, content) -> None:
    found = find_local_path(content)
    if found is not None:
        raise RecordError(f"{key} contains a laptop path ({found!r}...); replace it with a repo-relative path before publishing")


_NAME = r"[A-Za-z0-9][A-Za-z0-9._-]*"
_SLUG_PART = r"[a-z0-9][a-z0-9-]*"
# The publish boundary (doc 45 §3.1): only these record files become Notion record pages. The laptop-path
# scan above is a second layer against accidental leaks, not the boundary.
RECORD_KINDS = (
    ("ledger", re.compile(r"ledger\.jsonl")),
    ("run index", re.compile(rf"runs/(?P<run>{_NAME})/index\.md")),
    ("council record", re.compile(rf"runs/(?P<run>{_NAME})/council\.(?P<slug>{_SLUG_PART})(?:\.r[0-9]+)?\.{_SLUG_PART}(?:\.[0-9]+)?\.md")),
    ("stage snapshot", re.compile(rf"runs/(?P<run>{_NAME})/(?P<stage>{_NAME}?)\.snapshot(?:\.[0-9]+)?\.md")),
    ("harness manifest", re.compile(r"harness-manifest\.md")),
    ("document graph", re.compile(r"document-graph\.yml")),
    ("knowledge file", re.compile(rf"(?:domain|knowledge)/(?:{_NAME}/)*{_NAME}\.md")),
)


def record_kind(key: str):
    """(kind, match) for an allowed record key, or None."""
    for kind, pattern in RECORD_KINDS:
        m = pattern.fullmatch(key)
        if m:
            return kind, m
    return None


def _text(key: str, data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise RecordError(f"{key} is not UTF-8 text; only harness record files are published")
    if "\x00" in text or not text.strip():
        raise RecordError(f"{key} is empty or binary; only harness record files are published")
    return text


def _frontmatter(key: str, text: str) -> dict:
    m = FRONTMATTER.match(text)
    try:
        meta = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError:
        meta = None
    if not isinstance(meta, dict):
        raise RecordError(f"{key} has no YAML frontmatter mapping; a snapshot starts with the doc 33 template header")
    return meta


def check_record_shape(key: str, data: bytes, initiative: str | None = None) -> str:
    """Refuses anything that is not a known record file of the right shape; returns its kind."""
    found = record_kind(key)
    if not found:
        raise RecordError(f"{key} is not a harness record file (allowed: ledger.jsonl, runs/<run-id>/index.md, "
                          "runs/<run-id>/<stage>.snapshot.md, runs/<run-id>/council.<slug>.<part>.md, harness-manifest.md, "
                          "document-graph.yml, domain/ and knowledge/ markdown); it was not published")
    kind, m = found
    if kind == "ledger":
        raw = data.decode("utf-8", errors="replace")
        if "\r" in raw or (raw and not raw.endswith("\n")) or any(l != l.strip() or not l for l in raw.splitlines()):
            raise RecordError("ledger.jsonl is not canonical (one json object per line, LF endings, no blank lines); repair it first")
        validate = _ledger_validator()
        for n, line in enumerate(raw.splitlines(), 1):
            try:
                event = json.loads(line)
            except ValueError:
                raise RecordError(f"ledger.jsonl line {n} is not JSON")
            errs = validate(event) if isinstance(event, dict) else ["not a json object"]
            if errs:
                name = event.get("event_id") if isinstance(event, dict) else None
                raise RecordError(f"ledger.jsonl line {n} ({name or 'no event_id'}) fails the ledger schema: {'; '.join(errs)}")
        return kind
    text = _text(key, data)
    if kind == "run index":
        lines = text.splitlines()
        if not any(TABLE_ROW.match(a) and TABLE_RULE.match(b) for a, b in zip(lines, lines[1:])):
            raise RecordError(f"{key} has no index table (a header row and its |---| rule)")
    elif kind in ("stage snapshot", "council record"):
        meta = _frontmatter(key, text)
        want = {"run_id": m.group("run"),
                "stage": f"council.{m.group('slug')}" if kind == "council record" else m.group("stage")}
        if initiative:
            want["initiative"] = initiative
        for field in ("initiative", "run_id", "stage"):
            if not isinstance(meta.get(field), str) or not meta[field]:
                raise RecordError(f"{key} frontmatter has no {field}")
            # A stage file may drop the stage id's letter prefix: intake.snapshot.md holds stage A.intake.
            if field in want and meta[field] != want[field] and not (
                    field == "stage" and kind == "stage snapshot" and re.fullmatch(rf"[A-Z]\.{re.escape(want[field])}", meta[field])):
                raise RecordError(f"{key} frontmatter {field} is {meta[field]!r}, its path says {want[field]!r}")
    elif kind == "document graph":
        try:
            graph = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise RecordError(f"{key} is not valid YAML ({e.__class__.__name__})")
        if not isinstance(graph, dict):
            raise RecordError(f"{key} is not a YAML mapping")
    return kind


TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_RULE = re.compile(r"^\s*\|[\s:|-]*-[\s:|-]*\|\s*$")
_VALIDATE = []


def _ledger_validator():
    """The ledger writer's own schema check (framework/ledger/append.py), so publish and append agree."""
    if not _VALIDATE:
        import importlib.util
        spec = importlib.util.spec_from_file_location("harness_ledger_append", APPEND)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _VALIDATE.append(mod.validate)
    return _VALIDATE[0]


def b64_lines(data: bytes) -> str:
    enc = base64.b64encode(data).decode("ascii")
    return "\n".join(enc[i:i + B64_WIDTH] for i in range(0, len(enc), B64_WIDTH))


def record_body(key: str, data: bytes) -> str:
    """format harness-record/2: the file's exact bytes as base64, so nothing Notion does to whitespace or
    backticks can change it. The human-readable page is the separate doc 33 page."""
    return (f"{HEADER}\n\nrecord_key: {key}\nformat: harness-record/2\nencoding: base64\nsha256: {hashlib.sha256(data).hexdigest()}\n\n"
            f"{FENCE}text\n{b64_lines(data)}\n{FENCE}\n")


def ledger_body() -> str:
    return f"{HEADER}\n\nrecord_key: {LEDGER_KEY}\nformat: harness-record/2\nappend-only: one block per event, oldest first; each block is the json line then its sha256\n"


def ledger_append_block(line: str) -> str:
    line = line.strip()
    return f"\n{FENCE}text\n{line}\nsha256: {sha256(line)}\n{FENCE}\n"


def page_parent_ref(key: str) -> str:
    parts = key.split("/")
    if len(parts) >= 3 and parts[0] == "runs":
        return f"run:{parts[1]}"
    return "records-root"


NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DIRECTORY = getattr(os, "O_DIRECTORY", 0)


def initiative_parts(path: str, initiative: str) -> tuple:
    """(repo dir, names below .ai/<initiative>) for a path lexically under .ai/<initiative>/."""
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    # The outermost match: a nested .ai/<initiative> below it is reached through pinned descriptors.
    for i in range(1, len(parts)):
        if parts[i - 1] == ".ai" and parts[i] == initiative:
            return os.sep.join(parts[:i - 1]) or os.sep, parts[i + 1:]
    raise RecordError(f"{path} is not under .ai/{initiative}/")


def _open_below(dir_fd: int, name: str, directory: bool) -> int:
    """Open one name relative to an open directory, never following a symlink at that name."""
    try:
        fd = os.open(name, os.O_RDONLY | NOFOLLOW | os.O_NONBLOCK | (DIRECTORY if directory else 0), dir_fd=dir_fd)
    except OSError as e:
        try:
            link = stat.S_ISLNK(os.stat(name, dir_fd=dir_fd, follow_symlinks=False).st_mode)
        except OSError:
            link = False
        if link or e.errno == errno.ELOOP:
            raise RecordError(f"{name} is a symlink; export never follows links (copy the file in instead)")
        raise RecordError(f"cannot open {name}: {e.strerror}")
    st = os.fstat(fd)
    kind_ok = stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode)
    if not kind_ok or (not directory and st.st_nlink > 1):
        os.close(fd)
        if not kind_ok:
            raise RecordError(f"{name} is not a {'folder' if directory else 'regular file'}")
        raise RecordError(f"{name} is a hard link ({st.st_nlink} names); export only files that live in the record folder")
    return fd


def _open_path(dir_fd: int, names: list, directory: bool) -> int:
    """Walk names from dir_fd one component at a time with O_NOFOLLOW, so swapping any folder on the way
    for a symlink fails instead of redirecting the read. Closes nothing it was given."""
    fd = dir_fd
    try:
        for i, name in enumerate(names):
            nxt = _open_below(fd, name, directory or i < len(names) - 1)
            if fd != dir_fd:
                os.close(fd)
            fd = nxt
        return fd if fd != dir_fd else os.dup(dir_fd)
    except BaseException:
        if fd != dir_fd:
            os.close(fd)
        raise


def _open_initiative(repo: str, initiative: str) -> int:
    repo_fd = os.open(repo, os.O_RDONLY | DIRECTORY)
    try:
        return _open_path(repo_fd, [".ai", initiative], True)
    finally:
        os.close(repo_fd)


def _read_fd(fd: int) -> bytes:
    with os.fdopen(fd, "rb") as f:
        return f.read()


def plan_for_data(key: str, data: bytes, parent_id: str | None, initiative: str | None = None) -> dict:
    check_key(key)
    if os.path.basename(key) == PROFILE_KEY:
        raise RecordError("a harness profile is private: use profile-to-notion, never a shared record page")
    check_publishable(key, data)
    check_record_shape(key, data, initiative)
    parent = {"page_id": parent_id} if parent_id else {"resolve": page_parent_ref(key)}
    if key == LEDGER_KEY:
        lines = data.decode("utf-8").splitlines()
        content = ledger_body() + "".join(ledger_append_block(l) for l in lines)
    else:
        content = record_body(key, data)
    return {
        "tool": "notion-create-pages",
        "record_key": key,
        "args": {"parent": parent, "pages": [{"properties": {"title": os.path.basename(key)}, "content": content}]},
    }


def _walk(dir_fd: int, prefix: list, initiative: str, parent_id: str | None, plans: list) -> None:
    with os.scandir(dir_fd) as it:
        entries = sorted(it, key=lambda e: e.name)
    subdirs = []
    for entry in entries:
        if entry.is_symlink():
            raise RecordError(f"{'/'.join(prefix + [entry.name])} is a symlink; export never follows links (copy the file in instead)")
        if entry.is_dir(follow_symlinks=False):
            subdirs.append(entry.name)
        elif not (entry.name.startswith(".") or entry.name.endswith(".pyc") or entry.name == PROFILE_KEY):
            key = "/".join(prefix + [entry.name])
            data = _read_fd(_open_below(dir_fd, entry.name, False))
            if record_kind(key) is None:
                print(f"skipped {key}: not a harness record file, not published", file=sys.stderr)
                continue
            plans.append(plan_for_data(key, data, parent_id, initiative))
    for name in subdirs:
        sub = _open_below(dir_fd, name, True)
        try:
            _walk(sub, prefix + [name], initiative, parent_id, plans)
        finally:
            os.close(sub)


def to_notion(path: str, initiative: str, parent_id: str | None) -> list:
    """Plans for one file or a folder under .ai/<initiative>/. Every read goes through descriptors opened
    from the repo down with O_NOFOLLOW: no symlink, hard link, special file or outside path is read."""
    check_slug(initiative)
    if os.path.basename(path.rstrip(os.sep)) == PROFILE_KEY:
        raise RecordError("a harness profile is private: use profile-to-notion, never a shared record page")
    repo, names = initiative_parts(path, initiative)
    root_fd = _open_initiative(repo, initiative)
    try:
        parent_fd = _open_path(root_fd, names[:-1], True)
        try:
            if names:
                try:
                    mode = os.stat(names[-1], dir_fd=parent_fd, follow_symlinks=False).st_mode
                except OSError as e:
                    raise RecordError(f"cannot read {path}: {e.strerror}")
                if stat.S_ISLNK(mode):
                    raise RecordError(f"{path} is a symlink; export never follows links (copy the file in instead)")
                if not stat.S_ISDIR(mode):
                    return [plan_for_data("/".join(names), _read_fd(_open_below(parent_fd, names[-1], False)), parent_id, initiative)]
            fd = _open_path(parent_fd, names[-1:], True)
            try:
                plans = []
                _walk(fd, names, initiative, parent_id, plans)
                return plans
            finally:
                os.close(fd)
        finally:
            os.close(parent_fd)
    finally:
        os.close(root_fd)


def profile_to_notion(path: str, name: str) -> dict:
    with open(path, "rb") as f:
        data = f.read()
    # Private: creation_mode draft, and Notion refuses a parent with draft mode.
    return {"tool": "notion-create-pages", "record_key": PROFILE_KEY,
            "args": {"creation_mode": "draft", "pages": [{"properties": {"title": f"Harness profile ({name})"},
                                                          "content": record_body(PROFILE_KEY, data)}]}}


BLOCK_RE = re.compile(r"^```[a-z]*\n(.*?)\n```\s*$", re.S | re.M)


HEX64 = re.compile(r"[0-9a-fA-F]{64}")
OTHER_FENCE = re.compile(r"^(?: {1,3}`{3,}| {0,3}~{3,}| {0,3}`{4,})", re.M)
META = ("record_key", "format", "encoding", "sha256")


def _verified(recorded: str, actual: str) -> bool | None:
    """True or False for a real sha256, None when the page carries no usable one."""
    return actual == recorded.lower() if HEX64.fullmatch(recorded) else None


QUOTE_MARKERS = re.compile(r"^(?:\s*>)+\s*")


def _stray_ledger_line(page: str, matches: list):
    """(line number, what) for the first line outside the event blocks that could carry an event, in
    any decoded form and below any blockquote markers; None when there is none. An event the parser
    would not read must refuse the import, never vanish from it."""
    spans = [(m.start(), m.end()) for m in matches]
    pos = 0
    for n, line in enumerate(page.split("\n"), 1):
        start, pos = pos, pos + len(line) + 1
        if any(a <= start < b for a, b in spans):
            continue
        queue, seen = [(line, 0)], set()
        try:
            while queue:
                text, depth = queue.pop()
                if depth > MAX_NESTING or len(seen) > MAX_SCANNED_TEXTS:
                    raise _Unscannable("more nested content than the import decodes")
                for v in _variants(text):
                    if v in seen:
                        continue
                    seen.add(v)
                    bare = QUOTE_MARKERS.sub("", v).lstrip()
                    if bare[:1] in ("{", "[") or bare.startswith(("```", "~~~")):
                        return n, "a json line or code fence"
                    if "event_id" in v:
                        return n, "an event_id"
                    queue.extend((t, depth + 1) for t in _inner_texts(bare))
        except (_Unscannable, RecursionError) as e:
            return n, str(e) or "nested too deep"
    return None


def parse_record(page: str, allow_unverified: bool = False) -> tuple:
    """Returns (record_key, bytes, unverified): unverified names what imported without a hash (empty when
    everything was verified). Raises RecordError on anything it cannot prove, HashMismatch on a bad hash.
    Metadata is read only outside the code blocks, once each, and the page may hold nothing else that
    could carry content (another fence style, a stray json line), so nothing is silently dropped."""
    matches = list(BLOCK_RE.finditer(page))
    blocks = [m.group(1) for m in matches]
    outside, pos = [], 0
    for m in matches:
        outside.append(page[pos:m.start()])
        pos = m.end()
    outside = "".join(outside) + page[pos:]
    meta = {}
    for name in META:
        found = re.findall(rf"^{name}:[ \t]*(.*?)[ \t]*$", outside, re.M)
        if len(found) > 1:
            raise RecordError(f"record page repeats its {name} line; refetch it or supersede the page")
        meta[name] = found[0] if found else None
    if not meta["record_key"]:
        raise RecordError("not a harness record page: no record_key line")
    key = check_key(meta["record_key"])
    if re.search(r"^```", outside, re.M) or OTHER_FENCE.search(outside):
        raise RecordError(f"record page {key} has an unclosed, indented or non-backtick code fence; refetch the page")
    if key == LEDGER_KEY:
        stray = _stray_ledger_line(page, matches)
        if stray:
            raise RecordError(f"ledger page line {stray[0]} holds an event outside a code block ({stray[1]}); refetch the page")
        out, unverified = [], []
        for b in blocks:
            lines = [l for l in b.splitlines() if l.strip()]
            if not lines or len(lines) > 2 or (len(lines) == 2 and not lines[1].startswith("sha256:")):
                raise RecordError("ledger block is not one json line and its sha256 line")
            try:
                event = json.loads(lines[0])
            except ValueError:
                raise RecordError("ledger block does not hold a json event")
            if not isinstance(event, dict):
                raise RecordError("ledger block does not hold a json event")
            recorded = lines[1][len("sha256:"):].strip() if len(lines) == 2 else ""
            ok = _verified(recorded, sha256(lines[0]))
            if ok is False:
                raise HashMismatch("ledger event does not match its sha256 (edited by hand?)")
            if ok is None:
                if not allow_unverified:
                    raise RecordError(f"ledger event has no verifiable sha256 ({recorded or 'missing'}); pass --unverified to import it anyway and mark it unverified")
                # Hand-built event (no code execution): kept, and named in the provenance log.
                unverified.append(str(event.get("event_id") or f"block {len(out) + 1}"))
                lines[0] = lines[0].strip()
            out.append(lines[0] + "\n")
        return key, "".join(out).encode("utf-8"), unverified
    if len(blocks) != 1:
        raise RecordError(f"record page {key} has {len(blocks)} code blocks, expected 1")
    if meta["encoding"] == "base64":
        try:
            data = base64.b64decode("".join(blocks[0].split()), validate=True)
        except (ValueError, binascii.Error) as e:
            raise RecordError(f"{key}: base64 body is damaged ({e})")
    elif meta["encoding"] not in (None, "text"):
        raise RecordError(f"{key}: unknown encoding {meta['encoding']!r}")
    else:
        # Hand-built page (no code execution, doc 45 §3.3): plain text with the fence escape.
        data = (blocks[0].replace(ESCAPED_FENCE, FENCE) + "\n").encode("utf-8")
    recorded = meta["sha256"] or ""
    ok = _verified(recorded, hashlib.sha256(data).hexdigest())
    if ok is False:
        raise HashMismatch(f"{key} does not match its recorded sha256 (edited by hand?); supersede it instead")
    if ok:
        return key, data, []
    if not allow_unverified:
        raise RecordError(f"{key} has no verifiable sha256 ({recorded or 'missing'}); pass --unverified to import it anyway and mark it unverified")
    return key, data, [key]


def _same(a: str, b: str) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def safe_dest(root: str, initiative: str, key: str) -> str:
    """The file a record key names, refusing any key that reaches an existing file under another name:
    through a symlink, or by a spelling a case- or normalization-insensitive file system folds onto it.
    Either would let one record page overwrite another, the append-only ledger included."""
    base = os.path.realpath(os.path.join(root, ".ai", check_slug(initiative)))
    dest = base
    for part in check_key(key).split("/"):
        parent, dest = dest, os.path.join(dest, part)
        try:
            st = os.lstat(dest)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(st.st_mode):
            raise RecordError(f"{key} resolves through a symlink at {part}; import never writes through links")
        if part not in os.listdir(parent):
            spelled = [n for n in os.listdir(parent) if _same(os.path.join(parent, n), dest)]
            raise RecordError(f"{key} names {'/'.join(spelled) or 'an existing file'} by another spelling; import it under its own name")
    if os.path.commonpath([base, os.path.realpath(dest)]) != base:
        raise RecordError(f"{key} resolves outside .ai/{initiative}")
    try:
        st = os.lstat(dest)
    except FileNotFoundError:
        return dest
    if stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
        raise RecordError(f"{key} is a hard link ({st.st_nlink} names); import never writes through links")
    if key != LEDGER_KEY and _same(dest, os.path.join(base, LEDGER_KEY)):
        raise RecordError(f"{key} is the ledger under another name; import the ledger page as {LEDGER_KEY}")
    return dest


def log_unverified(root: str, initiative: str, key: str, data: bytes, source: str, unproven: list) -> None:
    """Persisted so later sessions mark decisions resting on this file unverified (doc 45 §3.1)."""
    log = safe_dest(root, initiative, UNVERIFIED_KEY)
    entry = {"record_key": key, "sha256": hashlib.sha256(data).hexdigest(), "source": source}
    if key == LEDGER_KEY:
        entry["unverified_events"] = unproven
    line = json.dumps(entry)
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            if line in f.read().splitlines():
                return
    with open(log, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def from_notion(page_path: str, root: str | None, initiative: str | None, to_stdout: bool,
                replace: bool = False, unverified: bool = False) -> int:
    with open(page_path, encoding="utf-8") as f:
        page = f.read()
    try:
        key, data, unproven = parse_record(page, unverified)
        if to_stdout or not initiative:
            sys.stdout.buffer.write(data)
            sys.stdout.flush()
            return 0
        root = root or repo_root() or os.getcwd()
        dest = safe_dest(root, initiative, key)
    except HashMismatch as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 3
    except RecordError as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 1
    source = os.path.basename(page_path)
    if key == LEDGER_KEY:
        return _import_ledger(dest, data, replace, root, initiative, source, unproven)
    if os.path.exists(dest):
        with open(dest, "rb") as f:
            current = f.read()
        if current == data:
            if unproven:
                log_unverified(root, initiative, key, data, source, unproven)
            print(f"unchanged {dest}" + (f" (unverified; listed in {UNVERIFIED_KEY})" if unproven else ""))
            return 0
        if not replace:
            print(f"refusing: {dest} exists with different content; keep both by superseding, or pass --replace", file=sys.stderr)
            return 1
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    if unproven:
        log_unverified(root, initiative, key, data, source, unproven)
        print(f"wrote {dest} (unverified; listed in {UNVERIFIED_KEY})")
        return 0
    print(f"wrote {dest}")
    return 0


def _import_ledger(dest: str, data: bytes, replace: bool, root: str, initiative: str, source: str, unproven: list) -> int:
    """Appends the page's new events to the local ledger and never truncates it. The read, the
    append-only check and the write happen under one lock (append.py takes the same one), so an event
    appended locally while the import runs is either seen and refused on, or written after the import."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    fd = os.open(dest, os.O_RDWR | os.O_CREAT | NOFOLLOW, 0o644)
    try:
        if fcntl:
            fcntl.flock(fd, fcntl.LOCK_EX)
        chunks = []
        while True:
            chunk = os.read(fd, 1 << 16)
            if not chunk:
                break
            chunks.append(chunk)
        current = b"".join(chunks)
        tag = f" (unverified; listed in {UNVERIFIED_KEY})" if unproven else ""
        if current == data:
            if unproven:
                log_unverified(root, initiative, LEDGER_KEY, data, source, unproven)
            print(f"unchanged {dest}{tag}")
            return 0
        if (current and not current.endswith(b"\n")) or not data.startswith(current):
            print(f"refusing: the ledger page would drop or rewrite events in {dest}; the ledger is append-only "
                  "(local events missing from the page stay local: append them to the page with ledger-entry first)", file=sys.stderr)
            return 1
        if current and not replace:
            print(f"refusing: {dest} exists with different content; keep both by superseding, or pass --replace", file=sys.stderr)
            return 1
        os.lseek(fd, 0, os.SEEK_END)
        view = memoryview(data)[len(current):]
        while view:
            view = view[os.write(fd, view):]
    finally:
        os.close(fd)
    if unproven:
        log_unverified(root, initiative, LEDGER_KEY, data, source, unproven)
    print(f"wrote {dest}{tag}")
    return 0


def ledger_entry(page_path: str, append_args: list, unverified: bool = False) -> int:
    with open(page_path, encoding="utf-8") as f:
        page = f.read()
    try:
        key, data, _ = parse_record(page, unverified)
    except HashMismatch as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 3
    except RecordError as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 1
    text = data.decode("utf-8")
    if key != LEDGER_KEY:
        print("refusing: not the ledger page", file=sys.stderr)
        return 1
    if not append_args:
        print("refusing: pass the append.py arguments after --", file=sys.stderr)
        return 1
    initiative = append_args[0]
    try:
        check_slug(initiative)
    except RecordError as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, ".ai", initiative, LEDGER_KEY)
        os.makedirs(os.path.dirname(ledger))
        with open(ledger, "w") as f:
            f.write(text)
        r = subprocess.run([sys.executable, APPEND, *append_args], env={**os.environ, "HARNESS_REPO_ROOT": tmp},
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            return r.returncode
        with open(ledger) as f:
            new_line = f.read().splitlines()[-1]
    try:
        check_publishable(LEDGER_KEY, new_line)
    except RecordError as e:
        print(f"refusing: {e}", file=sys.stderr)
        return 1
    print(json.dumps({"tool": "notion-update-page", "args": {"page_id": "LEDGER_PAGE_ID", "command": "insert_content",
                      "position": {"type": "end"}, "content": ledger_append_block(new_line)}}))
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect")
    d.add_argument("--surface", choices=SURFACES)
    d.add_argument("--profile")
    vp = sub.add_parser("validate-profile")
    vp.add_argument("path")
    t = sub.add_parser("to-notion")
    t.add_argument("path")
    t.add_argument("--initiative", required=True)
    t.add_argument("--parent-id")
    fr = sub.add_parser("from-notion")
    fr.add_argument("page")
    fr.add_argument("--root")
    fr.add_argument("--initiative")
    fr.add_argument("--stdout", action="store_true")
    fr.add_argument("--replace", action="store_true", help="overwrite a local file that differs")
    fr.add_argument("--unverified", action="store_true", help="import a page whose sha256 is unavailable")
    pr = sub.add_parser("profile-to-notion")
    pr.add_argument("path")
    pr.add_argument("--name", required=True)
    le = sub.add_parser("ledger-entry")
    le.add_argument("page")
    le.add_argument("--unverified", action="store_true", help="accept hand-built events whose sha256 is unavailable")
    a = p.parse_args(argv)
    if a.cmd == "detect":
        print(json.dumps(detect(a.surface, a.profile), indent=2))
        return 0
    if a.cmd == "validate-profile":
        try:
            print(json.dumps(validate_profile(a.path), indent=2))
        except RecordError as e:
            print(str(e), file=sys.stderr)
            return 2
        return 0
    if a.cmd == "to-notion":
        try:
            print(json.dumps(to_notion(a.path, a.initiative, a.parent_id), indent=2))
        except RecordError as e:
            print(f"refusing: {e}", file=sys.stderr)
            return 1
        return 0
    if a.cmd == "profile-to-notion":
        print(json.dumps(profile_to_notion(a.path, a.name), indent=2))
        return 0
    if a.cmd == "from-notion":
        return from_notion(a.page, a.root, a.initiative, a.stdout, a.replace, a.unverified)
    return ledger_entry(a.page, extra, a.unverified)


if __name__ == "__main__":
    sys.exit(main())
