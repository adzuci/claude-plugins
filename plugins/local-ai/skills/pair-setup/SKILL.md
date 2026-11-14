---
name: pair-setup
description: Manual-invocation only. Install, pair, verify, or remove NVIDIA Personal AI Router on two Macs (Apple Silicon or Intel) for local inference. Run via /local-ai:pair-setup.
argument-hint: host|client [install|pair|verify|uninstall]
disable-model-invocation: true
---

# PAIR Setup

Set up [NVIDIA Personal AI Router](https://github.com/NVIDIA/Personal-AI-Router)
(PAIR) across two Macs. Apple Silicon and Intel (x64) are both supported; the
installer picks the pinned disk image and digest for the machine's architecture. The host stores model weights and runs the
inference engine. The client sends requests to its own loopback address and PAIR
can forward them to the host over the LAN.

Run this skill on the host first, then on the client.

## Usage

```text
/local-ai:pair-setup host install
/local-ai:pair-setup client install
/local-ai:pair-setup host pair
/local-ai:pair-setup client verify
/local-ai:pair-setup host uninstall
```

`role` is required and must be `host` or `client`. When the action is omitted,
start with `verify` and recommend the next unfinished step.

## Stop Conditions

Before any installation, check the current PAIR release notes, its
[security documentation](https://github.com/NVIDIA/Personal-AI-Router/blob/develop/SECURITY.md),
and [tool-call issue #94](https://github.com/NVIDIA/Personal-AI-Router/issues/94).
Stop when the requested workload requires structured tool calls and that issue
is still open. Plain chat completions can work, but agent frameworks depend on
structured `tool_calls`.

Stop when either machine:

- is not macOS on Apple Silicon or Intel;
- is not owned by the user or explicitly authorized for this installation;
- is connected through an untrusted or isolated network; or
- cannot accept a persistent privileged helper and firewall changes.

## Trust Boundary

PAIR uses a six-digit PIN to bootstrap trust, then certificates and mutual TLS
for paired traffic. Discovery and some metadata remain LAN-visible. Pair only
while both machines and the network are trusted. Do not bind local inference
endpoints to non-loopback interfaces, forward the ports through a router, or put
an unauthenticated public reverse proxy in front of them.

PAIR installs a privileged helper. Dragging the app to Trash is not a complete
uninstall. Use the bundled uninstaller and verify that the helper is gone.

## Auto-update

PAIR updates itself. A pinned 0.1.1 install may become 1.0.0 and move from
`PAIR.app` to `NVIDIA PAIR.app` (same bundle ID and signing team), and its proxy
process is then `nvpair-proxy`. The doctor handles both layouts. Do not "fix" a
newer valid install by reinstalling the older pinned release.

## Hardware Notes

- Intel Macs have no GPU acceleration for inference and vLLM is unavailable.
  Use small models (1-4B parameters, for example `llama3.2:3b`) and make the
  Apple Silicon machine the host.
- Check free disk before pulling models and warn when under about 10 GB free.

## Actions

### Verify

Resolve the bundled script relative to this skill directory, then run:

```bash
scripts/pair_doctor.sh --role host
scripts/pair_doctor.sh --role client --probe
```

The probe is only local endpoint sanity. Bare Ollama can answer the same port.
Remote routing is proven only when PAIR's Jobs view says `Ran on` and names the
other machine.

### Install

Run the installer in read-only mode first:

```bash
scripts/pair_install.sh --check
```

Report the operating system, architecture, existing installation, pinned PAIR
version, and every planned write. After explicit confirmation, run:

```bash
scripts/pair_install.sh --apply
```

The installer downloads the exact reviewed disk image, verifies its SHA-256,
notarization ticket, Gatekeeper status, bundle identifier, signing team, and
application signature, then stages and atomically swaps the application.

On the host only, ask separately before stopping an existing Ollama service,
changing sleep settings, or pulling a model. Use `/local-ai:local-model-pick`
for the model choice. The client should not run its own engine because that can
cause requests to stay local.

Install the engine from PAIR's own **Install** button next to Ollama, not with
`brew install ollama`: on Intel Macs Homebrew may compile cmake from source and
saturate the CPU for a long time, and PAIR expects its engine on port 11435.
LM Studio's installer can fail with a 404 from `llmster.lmstudio.ai`; that is an
upstream download problem, so use Ollama. Pull a model through the engine port:

```bash
curl -s http://127.0.0.1:11435/api/pull -d '{"model":"llama3.2:3b","stream":false}'
```

The proxy on 11434 can take about 20 seconds to list a newly pulled model.

### Pair

PAIR's node service listens on TCP **14318** and advertises over mDNS. Ping and
ports 11434/11435 are not valid peer checks: ICMP is often blocked, and the
others are local endpoints. Check reachability with:

```bash
scripts/pair_doctor.sh --role host --peer <other-mac-ip>
```

If **Add node** lists the peer but `--peer` reports it unreachable, the peer's
firewall or router client isolation is blocking TCP 14318.

Confirm the user controls both machines and is on a trusted private LAN. Open
PAIR on both machines, choose **Add node**, and exchange the six-digit PIN while
both displays are visible. Discovery uses mDNS, so guest networks and access
point isolation can prevent the machines from seeing each other.

After pairing, send a plain completion request and verify the Jobs view names
the other machine. Do not claim success from `curl /v1/models` alone.

### Uninstall

Run `verify` first and explain that uninstall removes the PAIR app, privileged
helper, firewall rules, certificates, and application data. It does not remove
Ollama model weights. After explicit confirmation, run the bundled uninstaller:

```bash
sudo "/Applications/PAIR.app/Contents/Resources/installer-tools/uninstall-macos.sh" --purge
```

Then verify:

```bash
sudo launchctl print system/com.nvidia.nvpair.helper
```

Expect `Could not find service`. Offer, but do not automatically remove,
`~/Library/Caches/nvpair-updater`. Restore any service or sleep settings changed
during setup.

## Report

Return the role, action, PAIR version, artifact verification result, port owner,
engine state, local probe result, Jobs-view routing evidence, tool-call issue
status, and any manual or destructive steps that were skipped.
