---
name: pair-setup
description: Manual-invocation only. Install, pair, verify, or remove NVIDIA Personal AI Router on two Apple Silicon Macs for local inference. Run via /local-ai:pair-setup.
argument-hint: host|client [install|pair|verify|uninstall]
disable-model-invocation: true
---

# PAIR Setup

Set up [NVIDIA Personal AI Router](https://github.com/NVIDIA/Personal-AI-Router)
(PAIR) across two Apple Silicon Macs. The host stores model weights and runs the
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

- is not macOS on Apple Silicon;
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

### Pair

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
