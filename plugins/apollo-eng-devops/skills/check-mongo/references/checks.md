# check-mongo spec

Single source of truth for `/check-mongo`: humans, `scripts/`, and headless callers (Argus) all use it.
`tests/test_spec_sync.py` fails if the queries, thresholds, or check ids below differ from the code.
`<c>` = cluster (`main`, `accounts`, `contacts`, ...), `<w>` = restart window (default `1h`). Run as instant queries, per instance.

## Queries

| id | kind | PromQL |
| --- | --- | --- |
| uptime | instant | `mongodb_instance_uptime_seconds{cluster="<c>", role=~"mongos\|mongod\|mongoc"}` |
| restarts | instant | `resets(mongodb_instance_uptime_seconds{cluster="<c>", role=~"mongos\|mongod\|mongoc"}[<w>])` |
| up | instant | `up{cluster="<c>", role=~"mongos\|mongod\|mongoc", job="integrations/mongodb"}` |
| up_recent | instant | `max_over_time(up{cluster="<c>", role=~"mongos\|mongod\|mongoc", job="integrations/mongodb"}[24h])` |
| repl_lag | instant | `max by (cluster, role, instance, set) (mongodb_mongod_replset_member_replication_lag{cluster="<c>", role=~"mongod\|mongoc"})` |
| members_health | instant | `min by (cluster, role, instance, rs_nm) (mongodb_members_health{cluster="<c>", role=~"mongod\|mongoc"})` |
| oplog_window | instant | `mongodb_mongod_replset_oplog_head_timestamp{cluster="<c>", role=~"mongod\|mongoc"} - mongodb_mongod_replset_oplog_tail_timestamp{cluster="<c>", role=~"mongod\|mongoc"}` |
| connections | instant | `mongodb_connections{cluster="<c>", role=~"mongos", state="current"}` |
| mem_resident | instant | `mongodb_ss_mem_resident{cluster="<c>", role=~"mongos"}` |
| balancer_enabled | instant | `max by (cluster) (mongodb_mongos_sharding_balancer_enabled{cluster="<c>"})` |
| balancer_running | instant | `max_over_time(max by (cluster) (mongodb_mongos_sharding_chunks_is_balancer_running{cluster="<c>"})[30m:1m])` |
| shards_draining | instant | `max by (cluster) (mongodb_mongos_sharding_shards_draining_total{cluster="<c>"})` |
| host_mem_avail_pct | optional | `100 * mongodb_sys_memory_MemAvailable_kb{cluster="<c>", role=~"mongos\|mongod\|mongoc"} / mongodb_sys_memory_MemTotal_kb{cluster="<c>", role=~"mongos\|mongod\|mongoc"}` |

`optional` = empty result is UNKNOWN, not a failure. Units: `mongodb_ss_mem_resident` is **MB** (divide by 1024 for GiB when reporting); host memory is `mongodb_sys_memory_MemAvailable_kb` / `MemTotal_kb`.

## Thresholds

| threshold | default | meaning |
| --- | --- | --- |
| uptime_s | 1800 | uptime below this = recent restart (s) |
| reset_hosts | 2 | restarts on >= this many hosts = ESCALATE |
| lag_warn | 10 | replication lag s, WARN when strictly above |
| lag_escalate | 60 | replication lag s, ESCALATE when strictly above |
| oplog_warn_h | 24 | oplog window h, WARN when strictly below |
| oplog_escalate_h | 6 | oplog window h, ESCALATE when strictly below |
| conn_outlier_x | 2 | router connections > x * median = WARN only |
| missing_pct | 50 | % routers missing/zero connections = ESCALATE |
| mem_avail_warn | 15 | % host memory available, WARN when strictly below |
| mem_avail_escalate | 5 | % host memory available, ESCALATE when strictly below |
| expected_mongos | 0 | optional router-count override, 0 = unset; normally unneeded because of the 24h lookback |

## Checks

| check | uses | verdict rule (WARN / ESCALATE) |
| --- | --- | --- |
| router_up | up, up_recent, uptime, connections | ESCALATE if any router seen in the 24h lookback or any current series has no `up`>=1 now (`up==0` or absent). No routers seen = UNKNOWN. |
| members_up | up, up_recent | ESCALATE if any mongod/mongoc seen in the lookback is absent or `up==0` now. |
| mongos_connections | connections | ESCALATE if >= missing_pct % of routers are missing or 0; WARN if any missing/0 or > conn_outlier_x * median. |
| restarts | uptime, restarts | ESCALATE if >= reset_hosts hosts have uptime < uptime_s or resets > 0, or any mongod/mongoc did; WARN for one router. |
| replication_lag | repl_lag | Max lag > lag_warn = WARN, > lag_escalate = ESCALATE. |
| primaries | uptime | Primary = `rs_state` label is 1; ESCALATE if any `rs_nm` replset has != 1. No label = UNKNOWN. |
| member_health | members_health | ESCALATE if any value < 1. |
| oplog_window | oplog_window | Min (head - tail) in hours < oplog_warn_h = WARN, < oplog_escalate_h = ESCALATE. |
| balancer | balancer_enabled, balancer_running, shards_draining | ESCALATE if draining > 0 (no series = 0); WARN if enabled == 0 (semantics unverified). Enabled/running empty = UNKNOWN. |
| mongos_memory | mem_resident | INFO only, never scored. Report max resident in GiB. |
| host_memory | host_mem_avail_pct | Min available % < mem_avail_warn = WARN, < mem_avail_escalate = ESCALATE. Empty = UNKNOWN, and only WARN/ESCALATE count toward the overall status. |

Overall precedence: ESCALATE > WARN > UNKNOWN > OK (scored checks: all above except mongos_memory). Nothing scored = UNKNOWN.

## Rules

- Empty data is UNKNOWN, never OK.
- Check ALL routers, not just the alerting host; name each router and its state (up / down / absent).
- Never call an incident resolved until every router is `up==1` and stable for 15-30 min.
- `up==0`/absent means the process OR its exporter is down; only host access can tell which.
- Deploy-time connection spikes on routers are expected (leadgenie rolls out on every merge to master, not on a schedule); only headroom when they land matters.
- HUMAN-ONLY (needs host access, Argus cannot do these): OOM kill (`code=killed, status=9/KILL`, dmesg "Out of memory: Killed process") vs self-exit (`code=exited, status=N`, mongos log HEALTH "Fault manager progress monitor is terminating the server"), `journalctl`, `uptime -s`. List them under Couldn't verify.
