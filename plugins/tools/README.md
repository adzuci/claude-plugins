# Tools

`tools` collects small, safe setup skills for everyday tools. It starts with
**Tailscale**, so your own machines can reach each other over a private tailnet
when the local network will not let them (router client isolation, guest Wi-Fi,
different subnets) or when they are on different networks.

## Skills

| Skill | Purpose |
| --- | --- |
| `/tools:tailscale-setup` | Check, install, verify, and use Tailscale on macOS. Actions: `check`, `install`, `login`, `verify`, `peer`, `pair`, `uninstall`. |

## Install

```bash
claude plugin marketplace add adzuci/claude-plugins
claude plugin install tools@adzuci-plugins
```

Then run `/tools:tailscale-setup`.

For Codex:

```bash
codex plugin marketplace add adzuci/claude-plugins
codex plugin add tools@adzuci-plugins
```

## What the Tailscale skill does

- `check` is read-only: macOS and architecture, Homebrew, whether the
  `tailscale-app` cask exists, app/CLI present, backend state, your tailnet IP and
  MagicDNS name, and any other VPN app that could conflict.
- `install` runs `brew install --cask tailscale-app` only after you confirm.
- `login` is **always done by you in the Tailscale app**. The skill never handles
  auth keys or tokens and never asks you to paste one.
- `verify` and `peer <name-or-100.x> [--port 14318]` ping a peer over the tailnet
  and probe a TCP port (14318 is the NVIDIA PAIR node port).
- `pair` explains how to pair NVIDIA PAIR over the tailnet: mDNS discovery does
  not cross it, so use the peer's 100.x address or MagicDNS name, and confirm
  PAIR's Jobs view says `Ran on` with the other machine.
- `uninstall` removes the cask and reminds you to remove the device from the
  admin console.

## Safety model

- The bundled `scripts/tailscale_doctor.py` is **read-only**, uses only the
  standard library, and keeps an allow-list of fields from
  `tailscale status --json` (node keys, auth URLs, and other raw fields are
  dropped). Targets and ports are validated before anything is run.
- Nothing is installed, signed in, or changed without explicit confirmation, and
  `sudo` is never run for you.
- Do not expose inference ports with `tailscale funnel`; tighten tailnet ACLs if
  the tailnet is shared; keep the macOS firewall on with PAIR allowed.

## Development

```bash
python3 -m pip install -r tests/requirements.txt
python3 -m pytest plugins/tools -q
```

Tests run without network access or a real Tailscale install.
