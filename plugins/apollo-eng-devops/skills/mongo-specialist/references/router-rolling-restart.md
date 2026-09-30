# Router Rolling Restart

**Human-run runbook** for restarting any subset of a cluster's mongos routers, one at a
time. Agents cannot `ssh` and never run restarts; each restart needs the user's explicit
approval. The agent prints commands; the human runs them. Run
`/apollo-eng-devops:check-mongo <cluster>` before and after.

## Choose the subset

- Cluster and host numbers `<n>` (`mongos-<cluster>-<n>`), e.g. accounts 3,4,5.
- Batch size is fixed at 1. Never target all members of a role group (0-2 web/API,
  3-5 Sidekiq/cron) at once.
- Order: lowest-headroom first, unless its group-mates lack headroom.

## When a restart is the right remedy

- **Yes:** mongos memory is retained, not used. `db.serverStatus({tcmalloc:1})` shows
  `current_allocated` tiny vs resident, with `pageheap_free` large and
  `aggressive_decommit` 0. Example: accounts-3 held 48 GiB of free pages after the
  [2026-08-28 accounts cursor storm](https://apolloio.slack.com/archives/C69FJ9NEM/p1787897143144079).
- **No:** a DNS health-monitor exit (status 67) or a real allocation spike. See
  [`host-restart-triage.md`](host-restart-triage.md).
- A restart erases evidence. Capture first (step 3).

## Preconditions (all must hold)

- No production deploy running or queued (any merge to master triggers a leadgenie
  deploy): `gh run list --repo apolloio/leadgenie --workflow production.yml --limit 3`
- All cluster routers `up==1` ([routers dashboard](https://apolloio.grafana.net/d/haqcwjo/mongodb-routers)).
- Prod VPN on; no freeze; window 03:00-11:00 UTC (outside 4am-8pm PT).
- Never more than ONE router of a cluster down (the helper script enforces this).
- Never run the Ansible `restart mongos router` handler without `--limit <one host>`
  (prod playbooks have no `serial:`).

## Steps

Never print credential values in chat; show commands only in fenced blocks.

1. Approval: the user confirms cluster, routers, and window in chat.

1. Optional: mute the page first (depends on [#311](https://github.com/apolloio/claude-plugins/pull/311) merging). Skill, user-invoked: `/apollo-eng-devops:mute-alert create --matcher alertname="MongoDB Host has restarted" --matcher cluster=<cluster> --duration 90m --comment "planned router restarts" --ticket <INFRA-key>`,
   then `/apollo-eng-devops:mute-alert expire <id>` at the end. Fallback only: `plugins/apollo-eng-devops/skills/mute-alert/scripts/mute_alert.py`.
   A silence stops PAGES only (Argus posts and INCIDENT tickets still happen) and hides
   real failures, so all verification below stays mandatory.

1. Optional evidence capture (read-only): 2a, then 2b, then the mongosh block.

   **2a. Vault access.** Get the vault password from 1Password via DevOps into `~/.zp-vault`;
   `ANSIBLE_VAULT_IDENTITY_LIST` must include `prod@~/.zp-vault`. Test:

   ```bash
   F=ansible/inventory/production/group_vars/all/mongodb_secrets; ansible-vault view --vault-id prod@~/.zp-vault "$F" >/dev/null 2>&1 && echo OK
   ```

   **2b. Load credentials** (real terminal only; never echo or paste). Keys under
   `mongodb_secrets.security`: `mongo_admin_user`, `mongo_admin_password`,
   `mongo_admin_auth_database`. Helper:

   ```bash
   get(){ ansible-vault view --vault-id prod@~/.zp-vault "$F" | awk -v k="$1" '$1==k":"{print $2}' | tr -d "\"'"; }
   ```

   ```bash
   export MONGO_USER=$(get mongo_admin_user) MONGO_PASS=$(get mongo_admin_password) MONGO_AUTHDB=$(get mongo_admin_auth_database)
   ```

   Check lengths only (`echo ${#MONGO_USER}`). Then, on the router host:

   ```bash
   mongosh --quiet --host 127.0.0.1 --port <port> -u "$MONGO_USER" -p "$MONGO_PASS" --authenticationDatabase "$MONGO_AUTHDB" --eval 'const s=db.serverStatus({tcmalloc:1}); const t=s.tcmalloc.tcmalloc; const g=x=>(x/2**30).toFixed(1)+" GiB"; print("resident",g(s.mem.resident*2**20),"allocated",g(t.current_allocated_bytes),"heap",g(t.heap_size),"pageheap_free",g(t.pageheap_free_bytes),"uptime_s",s.uptime)'
   ```

   Run read-only on real routers [2026-09-29](https://apolloio.slack.com/archives/CCHSWB3DK/p1790705045896029); all fields worked.

1. Restart ONE router, then repeat 4-5 per host (unit `mongos-<cluster>.service`; startup ~10-25 s; a first-boot exit 67
   followed by a systemd auto-restart is not a failure by itself):

   ```bash
   gcloud compute ssh mongos-<cluster>-<n> --project indigo-lotus-415 --zone us-central1-c --internal-ip --command 'sudo systemctl restart mongos-<cluster>.service; sleep 25; systemctl is-active mongos-<cluster>.service; sudo journalctl -u mongos-<cluster>.service --since "-2min" --no-pager | tail -12'
   ```

1. Verify: `up==1`, uptime reset, resident memory small, connections at baseline within
   ~15 min, no Mongo error spike. Soak ~10 min, then repeat steps 3-4 for the next router.

A restarting router shifts ~50% of its load to its group-mates.

## Using the helper script

`scripts/rolling_restart.py` wraps these steps for a human. Default is a dry run (prints
exact commands, runs nothing):

```bash
python plugins/apollo-eng-devops/skills/mongo-specialist/scripts/rolling_restart.py --cluster accounts --hosts 3,4,5
```

`--execute` (human terminal only) runs one host at a time: refuses during a deploy or if
a peer is not `up==1` (`--skip-up-check` overrides, loudly), needs the typed hostname,
verifies `is-active`, `up==1`, uptime under 300 s, soaks (`--soak-min`), stops on first failure.

## Stop conditions

Stop if: router not `active` after ~2 min, connections do not recover, errors spike, or a
group-mate is under memory pressure. Journal: `code=killed status=9/KILL` is OOM;
`code=exited status=67` plus a `"c":"HEALTH"` log line is the health monitor.

## Rollback

None needed. If a router will not start, run `sudo systemctl start mongos-<cluster>.service`; read its journal.

## After

1. `unset MONGO_USER MONGO_PASS MONGO_AUTHDB`
1. Close any stale GCP memory incident; record in the ticket.
1. Follow-up: evaluate tcmalloc `tcmallocAggressiveMemoryDecommit` / `tcmallocReleaseRate`
   instead of repeated restarts. **Unverified:** router support; test on staging first.

## Links

- [Runbook: Mongo Operations Gradual Updates](https://app.notion.com/p/apolloio/Runbook-Mongo-Operations-Gradual-Updates-b276c1968a6f4157819129b5d4b86f87)
  (as last reviewed: mongod shards only; no router section)
- [Mongo Alerts Runbook](https://www.notion.so/1ceab2b3b496800a9c1eea5d8d3f67d6)
