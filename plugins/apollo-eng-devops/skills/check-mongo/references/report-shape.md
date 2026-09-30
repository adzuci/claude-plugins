# Report shape (headless / Argus)

ONE Slack post, \<=120 words: header, subtitle `_classification · impact · confidence 0.xx_`, bullets Alert (name each router: up|down|absent) / Root cause (verified only) / Couldn't verify / Next step, cc line. Never "resolved" until every router is up and stable 15-30 min. Preview: `evaluate.py --format argus`.

Below: 1) metrics only (contacts, 2026-09-29 ~18:39Z); 2) after a human read the hosts.

```text
*check-mongo · contacts · ESCALATE*
_host restarts · 3 routers reset, 7/7 up now · confidence 0.60_
- **Alert**: restarts ESCALATE: mongos-contacts-0, -1, -2. All 7 mongos (contacts-0..5, change-stream-0) up.
- **Root cause**: Not established from metrics.
- **Couldn't verify**: OOM kill vs self-exit (journalctl, dmesg, mongos log, `uptime -s`) is HUMAN-ONLY
- **Next step**: Human runs host-restart-triage on all routers. Not resolved until all up and stable 15-30 min.
cc: @oncall

*check-mongo · contacts · ESCALATE*
_router restarts · contacts-2 silent ~27 min, no reboot · confidence 0.80_
- **Alert**: contacts-0 killed 18:01:22Z; contacts-1 exited 18:10:07Z; contacts-2 exited 18:28:43Z.
- **Root cause**: contacts-0 kernel OOM kill. contacts-1/2 exit status 67 after mongos logged its fault manager terminating the server on a stuck DNS health check. Why DNS stalled: unproven.
- **Couldn't verify**: why DNS stalled; any link to the connection surge.
- **Next step**: Keep incident open until every router is up and stable 15-30 min.
cc: @oncall
```
