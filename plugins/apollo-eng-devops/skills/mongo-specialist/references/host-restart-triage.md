# Host Restart Triage

Use for the Grafana alert "MongoDB Host has restarted" (rule uid `cf32twnieez9ca`,
[alert](https://apolloio.grafana.net/alerting/grafana/cf32twnieez9ca/view)). Start with
`/apollo-eng-devops:check-mongo <cluster> --window 6h`; it covers steps 1 and 3 read-only.
Agents cannot `ssh`. Steps marked **human-run** are for the on-call on the host
(see [`gcloud-access.md`](gcloud-access.md)).

> **What we saw on 2026-09-29 (contacts, RCA pending)**
>
> - 3 of 7 mongos (6 routers + change-stream-0) restarted within ~28 min (process starts ~18:01Z, ~18:10Z, ~18:29Z per
>   `mongodb_instance_uptime_seconds`). Routers 3-5 and `change-stream-0` were untouched
>   (212-235 d uptime). No shard or config-server resets. Multi-host, so treat as an incident, not a single-host blip.
> - contacts-0: kernel OOM kill (human-verified). Journal: `code=killed, status=9/KILL`;
>   dmesg: `Out of memory: Killed process ... (mongos)`, `anon-rss` ~28.5 GiB of ~31.3 GiB
>   RAM. Resident memory was ~26 GB with ~2.6 GiB available before the kill.
> - contacts-1 and contacts-2: journal `code=exited, status=67/NOUSER`, then systemd
>   auto-restart ~5-6 s later. No OOM lines in dmesg or journal on either host. The mongos
>   log has `"c":"HEALTH"` "Fault manager progress monitor is terminating the server"
>   (cause: "Health observer DNS is still running since ...") before each exit. Gap from
>   that log line to the systemd exit: ~53 s on contacts-1, ~24.5 min on contacts-2
>   (unexplained).
> - contacts-2 also had no metrics (`up==0`, uptime series gone) from ~18:03Z to ~18:29Z,
>   and journald, ops-agent heartbeats and node_exporter were silent while the mongos log
>   was still being written at 18:04Z. The VM was not rebooted per GCE (no operations).
>   Host/network/logging silence; cause unproven.
> - A connection surge hit routers 0-2 from ~17:58Z (~14.5k to ~21k); contacts-3 stayed flat.
> - Root causes are **unproven**: not the DNS hang, not the surge, not why exit 67.
>   Slack has earlier exit-67 router restarts; do not assume the same cause:
>   [contacts-2 2024-04-03](https://apolloio.slack.com/archives/C02AER97N82/p1712148622859299),
>   [accounts-3/4/5 2026-08-28](https://apolloio.slack.com/archives/C69FJ9NEM/p1787897143144079)
>   (attributed there to multiTarget cursors).

## Steps

1. **Scope first; never assume isolated.** Check **every** router, not the alerting one:

   ```text
   /apollo-eng-devops:check-mongo <cluster> --window 6h --role mongos
   ```

   Restarts on 2+ hosts, or on any mongoc/mongod, are a major incident: declare with
   [`incident-response`](../../incident-response/SKILL.md). A rolling pattern points to a
   deploy, config push, or crash loop.

1. **Impact.** Open the
   [MongoDB Routers dashboard](https://apolloio.grafana.net/d/haqcwjo/mongodb-routers).
   `get_dashboard_panel_queries` returns `[]` for it, so query metrics directly.
   Connection, assert, and cursor spikes often precede a restart. Client error rate needs
   a Sentry or app-side check; Mongo metrics alone do not show it.

1. **GCE context (read-only).**

   ```text
   /apollo-eng-devops:check-mongo <cluster> --gce --window 6h
   ```

   - No reboot or stop/reset operation **suggests** the VM was not restarted. It does not
     prove a process-only restart: guest reboot, live migration and kernel panic create no
     compute operation.
   - An empty OOM section is not evidence of no OOM: the Cloud Logging filter was empty for
     contacts-0 although dmesg showed an OOM kill.

1. **Human-run: did the VM reboot?**

   ```bash
   uptime -s; journalctl --list-boots | tail -3
   ```

1. **Human-run: how did the process end?** The unit is `mongos-<cluster>.service`
   (confirmed `mongos-contacts.service`).

   ```bash
   journalctl -u mongos-<cluster>.service --since "<start>" --until "<end>" --no-pager | grep -E "Main process exited|killed|Started|Consumed|restart counter"
   ```

   `Consumed ... CPU time` and `restart counter is at N` are tells of a systemd auto-restart.

1. **Human-run: OOM evidence and disk.**

   ```bash
   sudo dmesg -T | grep -i -E 'out of memory|killed process'
   ```

   ```bash
   df -h
   ```

1. **Human-run: mongos log for health-monitor actions.** The log is
   `/var/log/mongodb/mongo-<cluster>-router.log`; a cron truncates files over 1G and it
   rotates daily, so check rotated files too.

   ```bash
   sudo grep '"c":"HEALTH"' /var/log/mongodb/mongo-<cluster>-router.log | tail -20
   ```

1. **Classify each restarted router** (each can differ):

   | Journal | Also look for | Reading |
   | --- | --- | --- |
   | `code=killed, status=9/KILL` | dmesg `Out of memory: Killed process` | Kernel OOM kill |
   | `code=exited, status=N` (N=67 seen) | HEALTH `Fault manager progress monitor is terminating the server` | mongos health monitor (DNS observer) ended the process |
   | `code=exited, status=N`, no HEALTH line | mongos log tail before the exit | Self-exit, reason unknown |
   | No exit line, no restart | `uptime -s` / `--list-boots` | Host reboot: use GCE operations and serial console |

   systemd's `/NOUSER` label on status 67 is only its sysexits name, not a user problem.
   Serial console: `gcloud compute instances get-serial-port-output` (human-run).

1. **Memory.** Units and queries are in [`checks.md`](../../check-mongo/references/checks.md)
   (`mongodb_ss_mem_resident` is MB). High memory alone is a clue, not proof. The team's
   main memory signal is the GCP Monitoring memory alerts.

1. **Resolve** only after 15-30 minutes stable **and** every router `up == 1`.

1. **Follow-up.** File an INFRA ticket for memory headroom, connection-surge or DNS
   findings when the evidence points there. Use
   [`systematic-debugging`](../../systematic-debugging/SKILL.md) for the root-cause pass.

## Hypotheses to test (unverified, not causes)

- GCP documents a per-VM limit on DNS queries to the metadata server. A reconnect storm
  after a router dies could plausibly stall lookups and trip the DNS health observer.
- Whether the ~24.5 min gap on contacts-2 came from host/network/logging silence or
  something in mongos shutdown is unknown.

## Detection gap

A router that hangs without exiting pages nobody; only its missing metrics show it.
Alerting on `up==0` or an absent mongos series is a follow-up (not in this skill).
See [`grafana-observability`](../../grafana-observability/SKILL.md).
