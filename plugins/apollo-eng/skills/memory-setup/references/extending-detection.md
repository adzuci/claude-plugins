# Extending Detection

Use this guide when `scripts/detect_memory_tooling.py` reports names in the `unknown` list that you want to handle explicitly (suppress the warning or add a cleanup handler).

## How Classification Works

Detection logic lives in `scripts/lib.py::classify_memory_tooling`. The function takes three inputs:

- `settings` — parsed `~/.claude/settings.json`
- `plugin_dirs` — names of directories under `~/.claude/plugins/marketplaces/` and `~/.claude/plugins/cache/`
- `mcp_names` — MCP server names from `settings.json` and `.mcp.json`

It returns:

```json
{
  "claude_mem": true | false,
  "unknown": ["some-memory-plugin", "..."]
}
```

**`claude_mem`** is true when any hook command, plugin dir name, or MCP name contains `claude-mem` or `thedotmack`.

**`unknown`** lists names that contain a memory-suggestive substring (`mem`, `memory`, `recall`, `knowledge`) but are not in the `_KNOWN_SAFE` set and are not already captured as `claude_mem`.

## Adding a Name to Known-Safe

If the flagged name is a false positive (e.g., an infra exporter that happens to contain "mem"), add it to `_KNOWN_SAFE` in `scripts/lib.py`:

```python
_KNOWN_SAFE: frozenset[str] = frozenset(
    {
        "session-end.sh",
        "claudian",
        "claude-mem",
        "thedotmack",
        "mem-exporter",
        "prometheus-mem",
        "your-new-safe-name",   # add here
    }
)
```

## Adding a New Cleanup Handler

Model the new script on `scripts/cleanup_claude_mem.py`:

1. Create `scripts/cleanup_<toolname>.py`.
1. Import helpers from `scripts/lib.py` (e.g., `strip_claude_mem_hooks` as a reference pattern).
1. Implement `run(home: Path, apply: bool, now: int) -> dict` — dry-run by default, `--apply` to mutate.
1. Print JSON to stdout; exit nonzero only on unrecoverable errors.
1. Back up `settings.json` before writing (copy to `settings.json.bak-<now>`).

## Adding a Detection Branch

In `classify_memory_tooling`, add a new signal set alongside `_CLAUDE_MEM_SIGNALS`:

```python
_YOUR_TOOL_SIGNALS = ("your-tool-id", "your-vendor-name")

your_tool = False
for name in all_names:
    if any(signal in name for signal in _YOUR_TOOL_SIGNALS):
        your_tool = True

return {"claude_mem": claude_mem, "your_tool": your_tool, "unknown": unknown}
```

Update `detect_memory_tooling.py` to surface the new key in its output.

## Adding a Test

Add a test case in `tests/test_memory_setup_lib.py` following the existing pattern:

```python
def test_classify_your_tool_detected():
    result = classify_memory_tooling({}, ["your-tool-id"], [])
    assert result["your_tool"] is True

def test_classify_your_tool_not_false_positive():
    result = classify_memory_tooling({}, ["prometheus-mem"], [])
    assert result.get("your_tool") is False
```

Run the suite before committing:

```bash
pip install -r tests/requirements.txt
python -m pytest -q
```
