# Client First-Run Fallbacks

Use this file only when `../SKILL.md` delegates to fallback install commands, assistant handoff snippets, or platform-specific setup details. `../SKILL.md` remains authoritative for bootstrap order, setup modes, auth gates, approval gates, and evidence capture.

## Official Sources

Use these sources for installation and assistant setup:

- Apollo CLI overview: `https://docs.apollo.io/docs/apollo-cli-overview`
- Apollo CLI releases: `https://github.com/apolloio/apollo-io-cli/releases/latest`
- Apollo CLI agent skill: `https://raw.githubusercontent.com/apolloio/apollo-io-cli/main/.claude/skills/apollo-cli/SKILL.md`

## When To Use This File

Use only the section needed:

- Homebrew is unavailable.
- The target workspace is Windows.
- The user needs a Claude Code, Cursor, Codex, Cowork, or Antigravity handoff snippet.
- The fast path installed the binary but `apollo --version` still fails.
- The login browser flow needs a short troubleshooting reminder.

If Homebrew is available, return to the fast path in `../SKILL.md`:

```bash
brew install apolloio/apollo-io-cli/apollo-io-cli
```

## Manual Install Commands

### macOS Apple Silicon Binary

```bash
curl -L -o apollo-macos-arm64 https://github.com/apolloio/apollo-io-cli/releases/latest/download/apollo-macos-arm64
chmod +x apollo-macos-arm64
sudo mv apollo-macos-arm64 /usr/local/bin/apollo
xattr -d com.apple.quarantine /usr/local/bin/apollo 2>/dev/null || true
apollo --version
```

### macOS Intel Binary

```bash
curl -L -o apollo-macos-x64 https://github.com/apolloio/apollo-io-cli/releases/latest/download/apollo-macos-x64
chmod +x apollo-macos-x64
sudo mv apollo-macos-x64 /usr/local/bin/apollo
xattr -d com.apple.quarantine /usr/local/bin/apollo 2>/dev/null || true
apollo --version
```

### Linux x64 Binary

```bash
curl -L -o apollo-linux-x64 https://github.com/apolloio/apollo-io-cli/releases/latest/download/apollo-linux-x64
chmod +x apollo-linux-x64
sudo mv apollo-linux-x64 /usr/local/bin/apollo
apollo --version
```

### Windows x64 Binary

```powershell
$userBin = "$env:USERPROFILE\bin"
New-Item -ItemType Directory -Force $userBin | Out-Null
Invoke-WebRequest `
  -Uri "https://github.com/apolloio/apollo-io-cli/releases/latest/download/apollo-windows-x64.exe" `
  -OutFile "$userBin\apollo.exe"

if (($env:Path -split ';') -notcontains $userBin) {
  [Environment]::SetEnvironmentVariable(
    "Path",
    "$userBin;" + [Environment]::GetEnvironmentVariable("Path", "User"),
    "User"
  )
  $env:Path = "$userBin;$env:Path"
}

apollo --version
```

If `apollo --version` does not work after the Windows PATH update, open a new PowerShell window and run it again.

### From Source

Use this only when Homebrew or the prebuilt binary is not available. Requires Node 18 or newer.

```bash
node --version
git clone https://github.com/apolloio/apollo-io-cli.git
cd apollo-io-cli
npm install
npm link
apollo --version
```

## Assistant Handoff Snippets

### Universal Starter Prompt

```text
I am building a GTM agent that needs Apollo data. Use the Apollo CLI workflow skill. Start with the fast path if Homebrew is available: brew install apolloio/apollo-io-cli/apollo-io-cli. If you can run terminal commands, run setup and summarize the result. If you cannot run commands, give me one command block at a time and ask me to paste the output. Once auth works, recommend the highest-value first Apollo workflow for my agent. Do not run enrichment, record changes, task creation, sequence changes, or sends without showing the exact command and getting approval.
```

### Claude Code Global Skill

```bash
mkdir -p ~/.claude/skills/apollo-cli
curl -fsSL https://raw.githubusercontent.com/apolloio/apollo-io-cli/main/.claude/skills/apollo-cli/SKILL.md \
  -o ~/.claude/skills/apollo-cli/SKILL.md
```

### Claude Code Per-Project Skill

```bash
mkdir -p .claude/skills/apollo-cli
curl -fsSL https://raw.githubusercontent.com/apolloio/apollo-io-cli/main/.claude/skills/apollo-cli/SKILL.md \
  -o .claude/skills/apollo-cli/SKILL.md
```

### Claude Code Windows Global Skill

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\apollo-cli" | Out-Null
Invoke-WebRequest `
  -Uri https://raw.githubusercontent.com/apolloio/apollo-io-cli/main/.claude/skills/apollo-cli/SKILL.md `
  -OutFile "$env:USERPROFILE\.claude\skills\apollo-cli\SKILL.md"
```

### Cursor, Codex, Cowork, Antigravity, Or Other Assistants

Add the official Apollo CLI skill URL to the assistant project instructions when the tool supports project instructions:

```text
https://raw.githubusercontent.com/apolloio/apollo-io-cli/main/.claude/skills/apollo-cli/SKILL.md
```

If the assistant reads `AGENTS.md`, add:

```bash
cat >> AGENTS.md <<'EOF'
Use the Apollo CLI skill from:
https://raw.githubusercontent.com/apolloio/apollo-io-cli/main/.claude/skills/apollo-cli/SKILL.md

Before running Apollo commands, follow the Apollo CLI workflow skill. Verify install and auth first, then require explicit approval before enrichment, record changes, task creation, sequence changes, or sends.
EOF
```

## Auth Troubleshooting

Use these reminders only when `apollo auth whoami` fails:

- Run `apollo auth login` in the same terminal environment where the assistant will run Apollo commands.
- If a browser opens, complete the browser login and return to the terminal.
- Re-run `apollo auth whoami`; this is the verification command.
- Never ask the user to paste tokens, cookies, or credential file contents.
