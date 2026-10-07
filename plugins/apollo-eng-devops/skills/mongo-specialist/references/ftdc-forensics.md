# FTDC Forensics

FTDC (`diagnostic.data`) is a 1Hz per-second recording of `serverStatus`, `/proc`, and disk
counters that mongod writes continuously. It is the only source for host-level behaviour on
Apollo's Mongo VMs, because node_exporter is allowlisted down to five filesystem/systemd
metrics and mongod.log ships nowhere. Decoding it is often the whole investigation.

## Retention: pull within 74 hours

At the `diagnosticDataCollectionDirectorySizeMB: 200` default, measured retention on a busy
email shard is **~74 hours** (21 files x 10MB spanning 73.6h). After that the file is gone and
the incident is unreconstructible. During INCIDENT-34256 the evidence was lost twice over:
aged off the host, and wiped from `/tmp` by the OS five days later.

- Pull the moment you know you need it.
- Land it in `~/incident-artifacts/<TICKET>/`, never `/tmp` and never a session scratchpad.
- Filenames are the file's **start** time and each spans ~3.5h, so the file covering 14:21 is
  probably stamped hours earlier. List the directory, do not glob on the incident hour.

## Pulling it (read-only)

`scp` runs as you and cannot elevate past the `drwx------ mongodb` data directory, so copy to
`/tmp` on the host first. The redirect runs as the SSH user, which avoids any `chown`.

```bash
gcloud compute ssh <host> --zone=<z> --project=<p> --internal-ip \
  --command='sudo ls -la /media/drive0/<replset>/db/diagnostic.data/'
gcloud compute ssh <host> --zone=<z> --project=<p> --internal-ip \
  --command='sudo cat /media/drive0/<replset>/db/diagnostic.data/<FILE> > /tmp/ftdc.bin'
gcloud compute scp '<host>:/tmp/ftdc.bin' ~/incident-artifacts/<TICKET>/ --internal-ip --zone=<z> --project=<p>
gcloud compute ssh <host> --zone=<z> --project=<p> --internal-ip --command='rm -f /tmp/ftdc.bin'
```

Nothing is written under `/media/drive0`.

## Decoding

`scripts/ftdc_decode.py`, no third-party dependencies.

```bash
python3 scripts/ftdc_decode.py ftdc.bin --gaps
python3 scripts/ftdc_decode.py ftdc.bin --start 2026-09-30T14:20:00 --end 2026-09-30T14:24:00 \
  --grep 'cpu|tcmalloc|connections|ticket|queue|repl\.executor' --out window.csv
```

`--gaps` alone is worth running first: a non-1s interval means the collector thread itself
stalled, which is a process- or host-level event, not anything on the wire.

Two decode rules the script enforces, both of which silently produce plausible-but-wrong
numbers if you hand-roll it:

- A BSON **Timestamp is two metric columns** (seconds, increment). Count it once and every
  later column shifts. Strings, ObjectIds and BinData contribute none.
- **Each chunk carries its own reference document.** Column sets change between chunks, so map
  by name, never by an index taken from the first chunk.

## Reading it

**Device busy is not device saturated.** `io_time_ms` near 1000/s means the device was busy,
nothing more. Read it with the completion counters:

| `io_time_ms`/s | `writes`/s | Meaning |
| --- | --- | --- |
| 1000 | 23,801 | Normal checkpoint burst |
| 1000 | 0 | **Device hang** |

In INCIDENT-34256 a parallel investigation ruled out disk because throughput was 17-47 MB/s
against a ~1,200 MB/s ceiling. The device was in fact completing **zero** writes for 14s while
reporting 100% busy, with `procs_blocked` at 42. `io_queued_ms` spiking afterwards is the
backlog draining, not the peak of load.

**Diff the peer member.** A single host's baseline is weak; the same shard's other member in
the same window is a real control. There, `-a` and `-b` were both SECONDARY with no primary to
sync from, and `ctxt/s` differed 166x (2,889 vs ~480,000). That is far harder evidence than
any comparison against the host's own history, and it also distinguishes a single-device fault
from a zone-wide one.

**Workload counters exonerate or implicate a query.** `queryExecutor.scanned`,
`opcounters.*` and `globalLock.activeClients.total` in the seconds *before* the event settle
whether a runaway query (the 2026-05-27 noncustomer pattern) was the trigger, without reading
any logs.
