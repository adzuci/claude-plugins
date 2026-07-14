# gcloud CLI and Mongo VM Access

For `gcloud logging read`, `gcloud compute ssh`, and any GCP-side forensics during a
Mongo incident. Stay read-only unless the user has explicitly approved a write.

## Install / update / auth

```bash
brew install --cask gcloud-cli          # or: brew install --cask google-cloud-sdk
gcloud components update                 # keep the SDK current
gcloud auth login                        # browser SSO
gcloud auth application-default login    # only if a tool needs ADC
```

## Projects

| Env | Project ID |
| --- | --- |
| prod | `indigo-lotus-415` |
| staging | `stage-23704` |

```bash
gcloud config set project indigo-lotus-415   # prod
gcloud config set project stage-23704         # staging
```

Prefer passing `--project` explicitly on each command so you never act on the wrong
env from a stale default.

## SSH to Mongo VMs

The flag that works at Apollo is **`--internal-ip`** (requires corp network / VPN routes
to the internal subnet). Do **not** reach for `--tunnel-through-iap` first:

```bash
gcloud compute ssh <vm> --project indigo-lotus-415 --zone us-central1-c --internal-ip
```

- mongos VM hostnames follow `mongos-<cluster>-<n>` (see
  [`mongo-clusters.md`](mongo-clusters.md) for the naming and counts).
- IAP tunneling (`--tunnel-through-iap`) needs `roles/iap.tunnelResourceAccessor`, which
  on-call **may not have**. Check SSH access **early** in an incident — a missing role or
  missing VPN route blocks all of the forensics below, and you want the escalation path
  named before you need it, not mid-incident.

## Read-only VM forensics block

Once on a suspected-sick mongos VM, this sequence proved decisive in a real SEV-2. All
read-only:

```bash
# kernel: OOM kills, network drops, NIC resets
dmesg -T | tail -100
# connection-tracking table pressure (nf_conntrack: table full drops connections)
sudo conntrack -S 2>/dev/null; cat /proc/sys/net/netfilter/nf_conntrack_count \
  /proc/sys/net/netfilter/nf_conntrack_max
# socket states to the mongos port — SYN-RECV / accept backlog buildup
ss -s; ss -tan 'sport = :27017' | awk '{print $1}' | sort | uniq -c
# accept-queue overflows and SYN cookies (rising ListenOverflows = backlog exhausted)
nstat -az | grep -iE 'ListenOverflow|ListenDrop|TCPSynRetrans|SyncookiesSent'
# file-descriptor ceiling for the mongos process (near-limit => refused connections)
pid=$(pgrep -n mongos); ls /proc/$pid/fd | wc -l; cat /proc/$pid/limits | grep 'open files'
# mongos log: connection churn, "connection refused", server-selection errors
sudo grep -iE 'connection (accepted|refused|ended)|slow query|ServerSelection' \
  /var/log/mongodb/mongos.log | tail -50
```

Read the `ListenOverflows`, `nf_conntrack_count` vs `_max`, and fd-count-vs-limit trio
together: a connection storm shows up as backlog overflow + conntrack pressure + fd
ceiling on the specific instance, while healthy peers stay flat.

## No-SSH fallback

If SSH/IAP access can't be obtained fast enough, use `gcloud logging read` for
kernel/mongos messages and the admin connection-pool endpoint — see
[`live-incident-mode.md`](live-incident-mode.md) §4.
