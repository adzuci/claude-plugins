# Glean CLI Setup

Use Glean CLI for Apollo prior art, policy, owner, and request discovery before public web research.

## Preflight

From the skill directory, run:

```bash
python3 scripts/check_dependencies.py
glean auth status
```

If `glean` is missing on macOS, install the official CLI and then authenticate:

```bash
brew install gleanwork/tap/glean-cli
glean auth login
```

For another operating system, use the releases from `https://github.com/gleanwork/glean-cli/releases/latest` rather than inventing a package-manager command. If the CLI is installed but signed out, run:

```bash
glean auth login
glean auth status
```

For CI, `GLEAN_API_TOKEN` is supported, but do not ask the caller to paste a token into chat or a report.

## Smoke Test

```bash
glean search --page-size 3 --fields results.document.title,results.document.url "Zip procurement guide"
```

Success means the command returns Apollo results with titles and URLs. If CLI setup is blocked, use Glean MCP or caller-provided links and label that fallback.

## Assessment Queries

Run a few narrow searches, not one broad query:

```bash
glean search --page-size 5 "<tool> approval"
glean search --page-size 5 "<tool> Zip"
glean search --page-size 5 "<business problem> existing tool"
glean search --page-size 5 --datasource slack "<tool>"
```

Inspect the strongest one or two results. Glean can find evidence and matching requests; it cannot create an approval record.
