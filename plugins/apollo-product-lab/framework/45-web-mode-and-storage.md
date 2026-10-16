# 45 — Web mode: where the record lives when there is no laptop

> Decision 2026-10-09 (Akansh). Designers want to run the harness from claude.ai, the Desktop app and the
> terminal. On claude.ai chat there is no file system, and on claude.ai/code the repo is a sandbox clone that
> is thrown away, so `.ai/<initiative>/runs/...` and `~/.claude/harness-profile.yml` cannot be the only home.
> The harness now has two storage modes, `local` and `notion`, with one canonical schema.

## 1. The rule

The files under `.ai/<initiative>/` stay the **canonical schema** on every host: same names, same
frontmatter, same ledger lines (docs 33, 41, `ledger/schema.json`). Notion mode stores each of those
files, byte for byte, as one **record page**. Nothing about a snapshot's content changes with the mode,
so a later sync Notion to local (or back) is a copy, not a translation.

The human-facing Notion page of doc 33 is unchanged and still required in both modes. In notion mode a
record therefore has two pages: the plain-language page people read (under `notion_parent`) and the
machine record page (under the records root, below). Only the human page is linked from Slack, PRs and
other human pages.

## 2. Which mode runs (detection)

Every record-writing skill resolves the mode before its first read or write, and says it in one line
(`storage: notion (surface claude-ai-chat; profile in notion)`). Order, first match wins:

1. **No file tools.** The session has no Bash and no Write tool (claude.ai chat, Desktop Chat): `notion`
   for records and profile. No script can run, so this check is the model's, not `storage.py`'s.
2. **Run the detector when Bash exists:** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/storage.py" detect [--surface S]`. It prints the surface, `storage`, `profile_store`, the steps to skip and the reasons.
   - `claude-code-cloud` (`CLAUDE_CODE_REMOTE` set): the home directory is not kept, so the profile is
     in Notion; records are `notion` unless the profile says `storage: local` and the cloned repo has
     `.ai/` (then they commit on the branch and team sync applies).
   - local terminal or Desktop Code tab: `local` inside a git repo (intake bootstraps `.ai/` if it is
     missing), unless the profile says `storage: notion`. Outside any git repo (no-repo mode, doc 43
     §10) records go to `notion` instead of being skipped. The profile is `local` when `~/.claude` is
     writable, else `notion`.
   - When the profile came from Notion, save it to a temp file and pass `--profile <file>` so its
     `storage:` override is read.
3. **Override:** `storage: local | notion` in the profile wins where it can work. `local` on a surface
   that cannot write files falls back to `notion` with the reason printed. On the web, where no profile
   file exists yet, onboarding asks the surface once (doc 36, `harness-onboard` question 0) and writes
   the profile to Notion (§4).

`--surface` is passed when the person told onboarding where they run; `HARNESS_SURFACE` does the same
from the environment.

## 3. The Notion layout

```
<notion_parent>                          human pages, as today (doc 33)
  Harness record: <initiative>           records root, one per initiative (notion_records_root)
    harness-manifest.md                  record page
    ledger.jsonl                         record page, append-only (§3.2)
    domain/frontend.md, knowledge/...    record pages
    Run <run-id>                         plain page; its body is the rendered index table
      index.md                           record page
      intake.snapshot.md                 record page
      council.<slug>.<lens>.md           record page (lens files are machine-only in both modes)
      council.<slug>.memo.md             record page (its human page sits under notion_parent)
```

### 3.1 Record page format (`harness-record/2`)

```
Machine record of the apollo-product-lab. Do not edit by hand; a new version supersedes it.

record_key: runs/<run-id>/D.design.snapshot.md
format: harness-record/2
encoding: base64
sha256: <sha-256 of the file's exact bytes>

(one fenced text block: the file's bytes as base64, 76 characters a line)
```

The body is base64 so nothing Notion does to whitespace, trailing newlines or backticks can change the
file; the round trip is byte for byte and the hash recorded in any snapshot that cites the file stays
valid. People read the doc 33 page, not this one. Rules `storage.py` enforces:

- `record_key` is the path relative to `.ai/<initiative>/`, plain names only: no leading `/`, no `.` or
  `..`, no laptop path, never `.ai/` or `.claude/`. `from-notion` also refuses a key that resolves
  outside `.ai/<initiative>/` (symlinks included).
- **The allowlist is the publish boundary.** `to-notion` publishes only these record files, each of
  which must also pass its shape check: `ledger.jsonl` (canonical, every line a JSON object that passes
  `ledger/append.py`'s schema check), `runs/<run-id>/index.md` (holds the index table),
  `runs/<run-id>/<stage>.snapshot.md` and its `.<n>` versions (doc 33 frontmatter whose `initiative`,
  `run_id` and `stage` match the path; `intake.snapshot.md` may hold `stage: A.intake`),
  `runs/<run-id>/council.<slug>.<part>.md` and its `.r<n>.` reruns for memos, lens files,
  inputs and decisions (the same frontmatter, `stage: council.<slug>`), and the setup records of the
  layout above: `harness-manifest.md`, `document-graph.yml` (a YAML mapping), and Markdown under
  `domain/` and `knowledge/` (non-empty UTF-8). A single file outside the list, or a listed file of the
  wrong shape, is refused with the file and the reason; a folder export skips files outside the list,
  names each on stderr, and refuses the whole export when a listed file fails its shape check.
- `to-notion` and `ledger-entry` also refuse content holding a laptop path. This scan is a best-effort
  second layer against **accidental** leaks, not a security control: it catches the paths below in the
  forms listed, and the allowlist above is what decides what may leave the laptop. The paths: `/Users/<name>`, `/home/<name>`,
  `/root`, `/Volumes`, `/mnt/<drive>`, any Windows drive with either slash, a UNC share (`\\server\share` or
  `//server/share`), a home or temp variable (`%USERPROFILE%`, `$HOME`, `$env:USERPROFILE`, `~/`), a temp
  folder (`/tmp`, `/private/...`, `/var/folders`) or a `file:` URL. The check reads every JSON and YAML
  key and value (whole file, each JSONL line, frontmatter, each fenced block) and every decoded form of
  the text (unicode, hex, URL, HTML and backslash escapes, full-width and zero-width characters, UTF-16,
  base64 and YAML `!!binary`), recursively, and rejects what it cannot finish scanning (too deep, too
  many layers, or no PyYAML: `pip install pyyaml`, listed in `scripts/requirements.txt`). A path inside an `http(s)` URL is a link, not a leak. Replace the path with
  a repo-relative one first.
- `to-notion` reads only regular files inside the real `.ai/<initiative>/` folder, opening each folder
  from the repo down with `O_NOFOLLOW`: it refuses a symlink anywhere (file, folder, or the folder
  itself, even one swapped in mid-export), a hard link, and a path outside the folder.
- `from-notion` reads metadata only outside the code blocks, once each; it refuses a page with a
  `~~~` or indented fence, or an event outside a block (in any decoded form, base64 included, blockquoted or not, named
  by its page line), and never shortens a local ledger (append-only, even with `--replace`): it appends
  only the page's new events, under the same file lock `ledger/append.py` takes, so a local event the
  page lacks makes the import refuse instead of vanishing. It also refuses a key that reaches an
  existing file through a symlink, a hard link or another spelling (case or Unicode folding), and a
  non-ledger key that names the ledger file. `ledger-entry` exits 3 on a hash mismatch, like `from-notion`.
- A harness profile is never a shared record: bulk export skips `harness-profile.yml`, and
  `to-notion` refuses it. Use `profile-to-notion` (§4).
- `from-notion` refuses (exit 3) when the bytes do not match `sha256`, and refuses (exit 1) when the
  hash is missing, malformed or `unavailable`, unless `--unverified` is passed; an unverified import is
  listed in `unverified-imports.jsonl` (key, sha256, source page) next to the record, and snapshot read
  mode reports every decision resting on a listed file as `in force, input unverified`.
- `from-notion` never overwrites a local file that differs: identical content is reported as
  `unchanged`, different content is refused unless `--replace`.

Pages are never edited: a new version is a new page with a `.<n>` suffix and `supersedes:`, as on disk.

**Hand-built pages** (claude.ai chat with code execution off): the body is the file as plain text in one
code block, a code fence inside it written as a backtick, a zero-width space and two backticks, and
`sha256: unavailable (no code execution)`. They import only with `--unverified`. A hand-built ledger
event is its json line with `sha256: unavailable (no code execution)` (or no hash line). With
`--unverified`, `from-notion` keeps it and lists its `event_id` under `unverified_events` in
`unverified-imports.jsonl`, and `ledger-entry` appends after it. A real hash that does not match is refused either way.

### 3.2 Ledger

One record page `ledger.jsonl`, append-only (the local file must be canonical, one JSON object per line
with LF endings, or `to-notion` refuses it): each event is one text code block holding the ledger line
and, on the next line, `sha256: <hash of that line>`, added with `notion-update-page` `insert_content` at
the end. `from-notion` refuses a block whose line does not match its hash or is not JSON. A Notion
database was considered and rejected: its column set would drift from `schema.json` and turn sync into a
translation. Validation is the same writer: `storage.py ledger-entry <fetched ledger page> -- <append.py arguments>` rebuilds the ledger in a temp directory, runs `append.py` (schema, stage ids, duplicate event
ids) and prints the one `insert_content` call to make.

### 3.3 Operations, per mode

| Operation | local | notion |
|---|---|---|
| profile read | `~/.claude/harness-profile.yml` | `notion-search` "Harness profile", keep pages created by the connected user (`notion-get-self`, or `notion-get-users` with `self`) whose body has `record_key: harness-profile.yml`, most recently edited first, then `from-notion --stdout` |
| profile write | heredoc to the file | first time: `storage.py profile-to-notion <file> --name <name>` prints a `notion-create-pages` call with `creation_mode: draft` and no parent (private); after that the one page is updated in place with `replace_content` |
| record write | write the file under `.ai/<initiative>/` | `to-notion <file> --initiative <slug> --parent-id <run or root page id>`, execute the printed `notion-create-pages` call; with no code execution, build the same body by hand per §3.1 and write `sha256: unavailable (no code execution)` |
| record read | read the file | `notion-fetch` the record page, `from-notion` |
| index row | append to `index.md` | supersede `index.md` and refresh the run page's rendered table |
| ledger event | `ledger/append.py` | `storage.py ledger-entry` then the printed `insert_content` |
| input hashes | `shasum -a 256` | the hash on the input's record page, or `unavailable` with code execution off; read mode marks unverifiable decisions `in force, input unverified` |
| team sync | `record-sync.sh pull/push` | not needed: Notion is shared; read the newest page version before writing |

`record-sync.sh` does nothing in notion mode (it is never called there). Its rules still hold in spirit:
read the newest record before you write, never overwrite someone else's page.

### 3.4 Sync between modes

`storage.py to-notion .ai/<initiative>` prints one create call per file (local to Notion).
`storage.py from-notion <page> --initiative <slug>` writes one file back (Notion to local), refusing on a
hash mismatch. A person moving from the web to a laptop pulls the run's record pages this way, commits
them on the feature branch, and switches the profile to `storage: local`. Two-way automatic sync is not
built; the hashes make a manual one safe.

## 4. Profile on the web

On a surface whose `profile_store` is `notion`, onboarding writes the same YAML as
`templates/harness-profile.yml` into a private `Harness profile (<name>)` page and records
`storage: notion`, `surface:` and `notion_records_root:` in it. Every later session on that surface finds
it with one search. Nothing secret is in it, in either mode.

The profile is the one record updated in place rather than superseded, because it holds settings, not
history. On claude.ai/code with `storage: local` (records committed on the branch, profile still in
Notion), save the fetched profile to a temp file and export `HARNESS_PROFILE=<that file>` before calling
`record-sync.sh`, which reads it first; otherwise the script finds no profile and treats the run as solo.

## 5. What each surface skips

| Surface | Storage default | Skipped, and what happens instead |
|---|---|---|
| terminal (Claude Code CLI) | local | nothing |
| Desktop **Code** tab | local | Fabric Studio previews (doc 35, observed broken there); use the CLI for them |
| claude.ai/code, Desktop cloud sessions | notion (profile always notion) | shunt and the Codex plugin (the adversary falls back per doc 35: Glean family on prd/design, same-family tagged on erd/plan/pr); Fabric Studio previews and Playwright against VPN previews; docker |
| claude.ai **chat** (uploaded Skills) | notion | everything above plus git, gh and `record-sync.sh`; the Agent tool, so council lenses run one after another in the same thread and the memo is tagged `degraded: in-thread lenses`; design-diff inventory, and the agent files `product-harness-init` would write (it records them in the manifest for the next Code session). Rerun a product-size council from a Code surface before the human decision. The plain-language check runs degraded in the same thread and is recorded `unverified: degraded plain-language check (same thread)` until a person confirms the page |

## 6. Designers on any surface

A designer shares a **Figma file, a Fabric Studio prototype (branch or Storyboard) or a Claude Design
project**. The harness never asks a designer for a PR or a staging or preview link, on any surface. A
designer may start from a thought or a PRD with no Figma; intake then runs the designer flow of doc 36.

## 7. Packaging for the web

`scripts/package.py` builds `dist/apollo-product-lab.zip` (the plugin, manifest at the archive root, a
`BUILD` file with the commit, for claude.ai/code and Desktop Customize → Plugins) and
`dist/skills/<skill>.zip` (claude.ai chat Skills: onboard, intake, snapshot, council, artifact-audit and
product-harness-init, so a new initiative can be bootstrapped in Notion; one folder per skill with
`SKILL.md`, the framework docs, the agent briefs and `scripts/storage.py`; frontmatter reduced to `name`
and a quoted `description`; plugin-root paths rewritten relative to the skill in every bundled text
file). It builds only from a git checkout, so ignored local files cannot ride along. See the plugin README, "Install By Surface".
