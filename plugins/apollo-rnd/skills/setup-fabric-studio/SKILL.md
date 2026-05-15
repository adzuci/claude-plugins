---
name: setup-fabric-studio
description: Set up Apollo's fabric-studio prototyping environment from scratch — installs Homebrew, git, GitHub CLI, and Node 22, authenticates with GitHub, clones the repo, and installs dependencies. Use when the user says "set up fabric-studio", "install fabric studio", "onboard me to fabric studio", or "I want to prototype with Fabric".
---

# Set up fabric-studio

End-to-end onboarding for Apollo's fabric-studio prototyping environment (`apolloio/fabric-studio`). Detect what's installed, install what's missing, authenticate, clone, install dependencies, and hand off to a new session.

This skill is macOS-first. On Linux/Windows, fall back to manual instructions in the [fabric-studio README](https://github.com/apolloio/fabric-studio#getting-started) and stop.

## Prerequisites the user must handle themselves

Surface these up front, before doing anything else:

1. **Connected to the Apollo VPN** — required for the private npm registry (`registry.ops-gcp.apollo.io`). Ask the user to confirm before continuing. If they skip and `npm install` fails on `@apolloio/fabric-core`, this is the cause.
1. **GitHub access to the Apollo org** — needed to clone. The skill will run `gh auth login` but cannot grant org membership; if `apolloio` isn't in their orgs after auth, send them to IT.

## Workflow

### 1. Preview what's about to happen

Before running anything, tell the user (in plain text):

> I'm going to:
>
> 1. Check what's already installed on your machine (read-only checks).
> 1. Install anything missing — Homebrew, git, GitHub CLI, nvm, Node 22.
> 1. Authenticate you with GitHub (opens a browser).
> 1. Clone `apolloio/fabric-studio`.
> 1. Run `npm install`.
>
> You'll see a Claude Code permission prompt for each command. For the read-only checks (e.g. `command -v`, `pwd`, `node --version`), you can hit **"always allow"** to silence prompts for that pattern going forward — they're safe to bless. For the install, auth, and clone steps, I'd recommend keeping the prompts on so you can see what's happening.
>
> Ready to start?

Wait for the user to confirm before proceeding.

### 2. Confirm destination

Default: clone into the user's current working directory. Run `pwd` and propose `$(pwd)/fabric-studio` as the destination — show the user the absolute path and confirm before cloning.

Override the default and ask the user explicitly if cwd is:

- `$HOME` (cloning a project into the home directory root is rarely what people want)
- `/`, `/tmp`, or any other system directory
- Inside another git repo (run `git rev-parse --show-toplevel 2>/dev/null` — if it returns a path, you're nested)

If `$(pwd)/fabric-studio` already exists and contains a `.git` folder, ask whether to use the existing checkout (still run steps 3–6 for tooling, then skip step 7 and go to step 8) or pick a different path.

### 3. Detect system tools

Run all four checks in a single Bash call so they execute together:

```
command -v brew; command -v git; command -v gh; [ -s "$HOME/.nvm/nvm.sh" ] && echo nvm-present || echo nvm-missing
```

### 4. Install what's missing (in order)

- **Homebrew** → `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`. Warn the user to expect a sudo password prompt. After install, add brew to the current shell's PATH per the installer's printed instructions (`eval "$(/opt/homebrew/bin/brew shellenv)"` on Apple Silicon).
- **git** → `brew install git`. On a fresh Mac without Xcode CLT, the OS may show an "Install Command Line Developer Tools" dialog. Tell the user to click Install and wait for it to finish before continuing.
- **gh** → `brew install gh`.
- **nvm** → `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash`, then source it in the current shell with `\. "$HOME/.nvm/nvm.sh"`. The pinned `v0.40.1` will eventually go stale — bump it to the latest from [nvm releases](https://github.com/nvm-sh/nvm/releases) when you notice it's drifted.

### 5. Install Node 22

```
nvm install 22 && nvm use 22
```

Verify with `node --version` (expect `v22.x`).

### 6. Authenticate with GitHub

Run `gh auth status`. If not authenticated:

```
gh auth login
```

Walk the user through the prompts: **GitHub.com → HTTPS → Authenticate with browser**. Tell them to copy the one-time code shown in the terminal, then paste it into the browser tab that opens.

After auth, confirm Apollo org membership:

```
gh api user/orgs --jq '.[].login'
```

If `apolloio` is not in the output, stop and tell the user to request org access (Slack `#it-helpdesk` or similar) — re-invoke the skill once granted.

### 7. Clone the repo

```
gh repo clone apolloio/fabric-studio <destination>
```

### 8. Install dependencies

```
cd <destination>
nvm use
npm install
```

If `npm install` errors fetching `@apolloio/fabric-core`, the user is almost certainly not on the Apollo VPN. Stop, tell them, resume from this step once VPN is on.

### 9. Hand off

The current Claude Code session is bound to its starting directory and cannot move. The user has to open a new session at the cloned path.

Tell them, in plain text (substitute the real path):

> Done — fabric-studio is cloned at **`<absolute-path>`** and dependencies are installed.
>
> Next steps — open a new Claude Code session pointing at that directory, then type `/start`:
>
> - **CLI:** `cd <absolute-path> && claude`
> - **Desktop app:** start a new session and select **`<absolute-path>`** as the working directory from the project/directory picker.

Do not type `/start` from this session — it cannot act on the new project.

## What this skill does NOT do

- Cannot open a new Claude Code session in the cloned directory (sessions are bound to starting cwd).
- Does not run `/start` — that's the user's first action in the new session.
- Does not create a `prototype/*` branch — `/start` in the new session handles that.
