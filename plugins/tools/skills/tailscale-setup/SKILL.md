---
name: tailscale-setup
description: Manual-invocation only. Check, install, verify, and use Tailscale on macOS so your own machines (including NVIDIA PAIR peers) can reach each other over a private tailnet. Run via /tools:tailscale-setup.
argument-hint: '[check|install|login|verify|peer|pair|uninstall]'
disable-model-invocation: true
---

# Tailscale Setup

Connect your own Macs over a private [Tailscale](https://tailscale.com/) tailnet
when the local network will not let them talk (router client isolation, guest
Wi-Fi, different subnets) or when they are on different networks. Tailscale is a
WireGuard-based mesh VPN: every device gets a `100.x.y.z` address and an
optional MagicDNS name.

Resolve bundled scripts relative to this skill directory (`scripts/`). The
bundled `tailscale_doctor.py` is **read-only** and prints JSON. Every state
change (install, login, uninstall) is performed with the user's explicit
confirmation, and **login is always done by the user in the Tailscale app**.

## Rules

- Never ask for, accept, or handle Tailscale auth keys, API keys, or tokens. Never
  paste one into chat, a command line, or a file.
- Sign-in happens in the Tailscale app (browser flow). Do not automate it.
- Approve the VPN/network extension in System Settings yourself; the skill only
  tells the user where to click.
- No `tailscale up --authkey`, no `tailscale serve`/`funnel`, and no
  `--ssh` unless the user asks for it and understands the exposure.

## Actions

With no argument, run `check` and recommend the next unfinished step.

### check (read-only)

```bash
python3 scripts/tailscale_doctor.py check
```

Report as a table: macOS, architecture (Apple silicon or Intel), Homebrew,
whether the `tailscale-app` cask exists, app installed, CLI path, backend state,
own tailnet IP and MagicDNS name, other VPN apps found (NordVPN, WARP, and so
on), and the suggested `next` step. The Tailscale CLI is on `PATH` when
installed with the Homebrew cask or at
`/Applications/Tailscale.app/Contents/MacOS/Tailscale`.

### install

Only when `check` says `next: install`. Explain what it does: downloads the
Tailscale app, installs a VPN/network extension, and starts a background
service. After explicit confirmation:

```bash
brew install --cask tailscale-app
```

Confirm the cask name first with `brew info --cask tailscale-app` (the `check`
action does this). If Homebrew is missing or the cask is unavailable, point to
<https://tailscale.com/download/mac> and let the user install by hand. Do not run
`sudo` on the user's behalf.

### login (user-driven)

Tell the user to do this themselves:

1. Open **Tailscale** from Applications (menu bar icon), click **Log in**, and
   sign in with the account that owns the tailnet.
2. When macOS asks, allow the **VPN configuration** and approve the
   **network/system extension** in **System Settings → General → Login Items &
   Extensions** (or **Privacy & Security**, depending on the macOS version).
3. Make sure both Macs sign in to the **same tailnet** (same account or a shared
   device).

Then run `check` again; expect `backend_state: Running`.

### verify

```bash
python3 scripts/tailscale_doctor.py verify [--peer <name-or-100.x>]
```

Passes only when the backend is `Running`, this Mac has a `100.64.0.0/10`
address, and a `tailscale ping` to a peer succeeds. A `direct` path means peers
talk to each other directly; `relay` means traffic goes through Tailscale's
DERP relays (works, but slower).

### peer

```bash
python3 scripts/tailscale_doctor.py peer <name-or-100.x> [--port 14318]
```

Pings the peer over the tailnet, then probes TCP with
`nc -vz -G 3 <ip> <port>`. The default port `14318` is the NVIDIA PAIR node
port. Read the result:

- `ping.ok` false: no tailnet path. Check both are `Running` in the same tailnet
  and the peer is online.
- `ping.ok` true, `tcp_open` false: the tailnet works, but the service is not
  reachable. Is PAIR running on the peer, and does a firewall block the port?
- Both true: ready to pair.

### pair (NVIDIA PAIR over the tailnet)

PAIR discovers nodes with mDNS, which **does not cross the tailnet**. Use the
peer's address instead:

1. Run `peer <peer> --port 14318` on both Macs and get `ok: true` each way.
2. Open PAIR on both, choose **Add node**, and enter the peer's **100.x address
   or MagicDNS name** if the UI offers manual entry; otherwise keep both Macs on
   the same LAN for discovery and use Tailscale only for the data path.
3. Exchange the six-digit PIN while both screens are visible.
4. Prove routing with a plain completion from the client. PAIR's **Jobs** view
   must say `Ran on` and name the other machine. `GET /v1/models` alone proves
   nothing, because a local Ollama answers it too.

See `/local-ai:pair-setup` for the PAIR install, trust boundary, and tool-call
limitations.

### uninstall

Confirm with the user first. Quit the app, then:

```bash
brew uninstall --cask tailscale-app
```

Tell the user to remove the machine from the admin console
(<https://login.tailscale.com/admin/machines>) so it stops counting as a device,
and to delete the extension under System Settings if it lingers. Note that other
Macs lose their route to this one.

## Security notes

- **ACLs:** the default tailnet policy lets every device reach every other
  device on all ports. Tighten it in the admin console (for example allow only
  your own devices to reach port `14318`) if the tailnet is shared.
- **Never expose inference ports publicly.** Do not use `tailscale funnel` (or a
  public `serve`) for PAIR, Ollama (`11434`), LiteLLM, or any model endpoint.
- **Keep the PAIR firewall guidance:** enable the macOS firewall and allow
  "NVIDIA PAIR". Tailscale does not replace PAIR's PIN and mutual-TLS trust.
- **Key expiry:** devices re-authenticate periodically (default about 180 days).
  Disable expiry only for always-on machines you control.
- **Tailscale SSH:** leave it off unless you deliberately want it.
- Remove devices you no longer use from the admin console.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `next: start-the-app` / "failed to connect to local tailscaled" | App not running or extension not approved | Open Tailscale; approve the VPN configuration and extension in System Settings |
| `backend_state: NeedsLogin` | Not signed in | Log in from the app (user action) |
| `backend_state: Stopped` | Tailscale turned off | Toggle it on from the menu bar |
| `NeedsMachineAuth` | Tailnet requires device approval | Approve the machine in the admin console |
| Peer missing from `status` | Different account/tailnet | Sign both Macs into the same tailnet |
| `ping` works, `nc` fails | Service not listening or firewall | Start PAIR on the peer; check firewall rules and the port |
| Everything times out with NordVPN or another VPN on | Two VPNs fighting over routes/DNS | Quit the other VPN or enable its LAN/local-network allowance, then retry |
| LAN `nc` times out but tailnet `peer` works | Router client isolation or different subnet | Use the 100.x/MagicDNS address; or disable isolation on the router |
| `relay` path, slow | Direct connection blocked by NAT | Usually fine; open UDP 41641 or enable UPnP on the router for a direct path |

## Report

Return the action run, `backend_state`, this Mac's tailnet IP and MagicDNS name,
peers seen, ping path (`direct` or `relay`) and latency, TCP probe result and
port, and any manual step the user still has to do (sign-in, extension approval,
ACL review).
