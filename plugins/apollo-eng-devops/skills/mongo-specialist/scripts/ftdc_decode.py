#!/usr/bin/env python3
"""Decode MongoDB FTDC (diagnostic.data) metric chunks to CSV.

No third-party deps. Reads one or more FTDC files, emits one row per 1Hz sample.

The usual decode bug this avoids: the number of metric columns is NOT the number
of keys in the reference document. Walk the reference doc in document order and
count BSON Timestamp as TWO metrics (seconds, increment); Double/Int32/Int64/Bool/
Date as one each; everything else (String, ObjectId, BinData, Null, Decimal128,
MinKey/MaxKey, Regex, Code) as zero. Get that wrong and every column shifts.

Usage:
  ftdc_decode.py metrics.2026-09-30T14-00-00Z-00000 --out ftdc.csv
  ftdc_decode.py metrics.* --start 2026-09-30T14:20:00 --end 2026-09-30T14:24:00 \
      --grep 'cpu|tcmalloc|connections|tickets|queue|network' --out window.csv
  ftdc_decode.py metrics.* --gaps        # just print sampling-interval gaps
"""

import argparse
import csv
import datetime as dt
import glob
import struct
import sys
import zlib

# ---------------------------------------------------------------- BSON reader

DOC, ARRAY = 0x03, 0x04


def _cstring(buf, i):
    j = buf.index(b"\x00", i)
    return buf[i:j].decode("utf-8", "replace"), j + 1


def parse_doc(buf, off=0):
    """Return (ordered list of (key, type, value), end_offset)."""
    (size,) = struct.unpack_from("<i", buf, off)
    end = off + size
    i = off + 4
    out = []
    while i < end - 1:
        t = buf[i]
        i += 1
        key, i = _cstring(buf, i)
        if t == 0x01:  # double
            (v,) = struct.unpack_from("<d", buf, i)
            i += 8
        elif t == 0x02 or t == 0x0D or t == 0x0E:  # string, code, symbol
            (n,) = struct.unpack_from("<i", buf, i)
            v = buf[i + 4 : i + 4 + n - 1].decode("utf-8", "replace")
            i += 4 + n
        elif t in (DOC, ARRAY):
            v, i = parse_doc(buf, i)
        elif t == 0x05:  # binary
            (n,) = struct.unpack_from("<i", buf, i)
            sub = buf[i + 4]
            v = buf[i + 5 : i + 5 + n]
            i += 5 + n
            v = (sub, v)
        elif t == 0x06 or t == 0x0A:  # undefined, null
            v = None
        elif t == 0x07:  # objectid
            v = buf[i : i + 12].hex()
            i += 12
        elif t == 0x08:  # bool
            v = bool(buf[i])
            i += 1
        elif t == 0x09:  # datetime (ms)
            (v,) = struct.unpack_from("<q", buf, i)
            i += 8
        elif t == 0x0B:  # regex
            _, i = _cstring(buf, i)
            _, i = _cstring(buf, i)
            v = None
        elif t == 0x0C:  # dbpointer
            (n,) = struct.unpack_from("<i", buf, i)
            i += 4 + n + 12
            v = None
        elif t == 0x0F:  # code_w_scope
            (n,) = struct.unpack_from("<i", buf, i)
            i += n
            v = None
        elif t == 0x10:  # int32
            (v,) = struct.unpack_from("<i", buf, i)
            i += 4
        elif t == 0x11:  # timestamp -> (increment, seconds) on the wire
            inc, sec = struct.unpack_from("<II", buf, i)
            i += 8
            v = (sec, inc)
        elif t == 0x12:  # int64
            (v,) = struct.unpack_from("<q", buf, i)
            i += 8
        elif t == 0x13:  # decimal128 - not a metric
            i += 16
            v = None
        elif t in (0xFF, 0x7F):  # minkey, maxkey
            v = None
        else:
            raise ValueError(f"unknown BSON type 0x{t:02x} at {i}")
        out.append((key, t, v))
    return out, end


def iter_bson(buf):
    off = 0
    n = len(buf)
    while off < n:
        (size,) = struct.unpack_from("<i", buf, off)
        if size <= 0 or off + size > n:
            break
        doc, end = parse_doc(buf, off)
        yield doc
        off = end


def get(doc, key):
    for k, _t, v in doc:
        if k == key:
            return v
    return None


# ------------------------------------------------- reference-doc metric walk


def walk_metrics(doc, prefix=""):
    """Yield (dotted_name, initial_value) in exact FTDC column order."""
    for key, t, v in doc:
        name = f"{prefix}{key}"
        if t in (DOC, ARRAY):
            yield from walk_metrics(v, name + ".")
        elif t == 0x01:  # double -> truncated to int64 by FTDC
            yield name, int(v)
        elif t == 0x08:  # bool
            yield name, 1 if v else 0
        elif t == 0x09:  # datetime
            yield name, v
        elif t == 0x10 or t == 0x12:  # int32 / int64
            yield name, v
        elif t == 0x11:  # timestamp -> TWO columns
            sec, inc = v
            yield name, sec
            yield name + ".inc", inc
        # everything else contributes no column


# --------------------------------------------------------------- varint + RLE


def read_varint(buf, i):
    shift = 0
    result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, i
        shift += 7


MASK64 = (1 << 64) - 1


def decode_chunk(blob):
    """blob = BinData payload of a type-1 doc. Returns (names, rows)."""
    (_uncompressed_len,) = struct.unpack_from("<I", blob, 0)
    raw = zlib.decompress(blob[4:])

    ref, off = parse_doc(raw, 0)
    cols = list(walk_metrics(ref))
    names = [n for n, _ in cols]
    base = [v for _, v in cols]

    nmetrics, nsamples = struct.unpack_from("<II", raw, off)
    off += 8

    if nmetrics != len(names):
        raise ValueError(
            f"metric count mismatch: header says {nmetrics}, reference doc walk "
            f"produced {len(names)}. Columns would be misaligned; refusing to emit."
        )

    # column-major deltas with zero run-length encoding
    deltas = [[0] * nsamples for _ in range(nmetrics)]
    zeros_left = 0
    i = off
    for m in range(nmetrics):
        for s in range(nsamples):
            if zeros_left:
                zeros_left -= 1
                continue
            v, i = read_varint(raw, i)
            if v == 0:
                run, i = read_varint(raw, i)
                zeros_left = run  # this sample is 0, plus `run` more
                continue
            deltas[m][s] = v

    rows = [list(base)]
    cur = list(base)
    for s in range(nsamples):
        for m in range(nmetrics):
            d = deltas[m][s]
            if d:
                cur[m] = (cur[m] + d) & MASK64
        rows.append(list(cur))
    return names, rows


# ------------------------------------------------------------------- driver


def ms_to_iso(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).isoformat(
        timespec="milliseconds"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", help="CSV output path (default stdout)")
    ap.add_argument("--start", help="ISO8601 UTC inclusive, e.g. 2026-09-30T14:20:00")
    ap.add_argument("--end", help="ISO8601 UTC exclusive")
    ap.add_argument("--grep", help="regex; keep only columns whose name matches")
    ap.add_argument(
        "--gaps",
        action="store_true",
        help="print sampling intervals != 1s and exit (the FTDC stall signature)",
    )
    args = ap.parse_args()

    paths = []
    for pat in args.files:
        paths.extend(sorted(glob.glob(pat)) or [pat])

    def bound(s):
        if not s:
            return None
        return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp() * 1000

    lo, hi = bound(args.start), bound(args.end)

    import re

    keep = re.compile(args.grep) if args.grep else None

    # Chunks carry their own reference doc, so the column set can change between
    # chunks. Map by NAME per chunk, never by index across chunks.
    union = []
    seen = set()
    per_chunk = []
    stamps = []

    for p_ in paths:
        with open(p_, "rb") as fh:
            buf = fh.read()
        for doc in iter_bson(buf):
            if get(doc, "type") != 1:
                continue
            data = get(doc, "data")
            if not data:
                continue
            _sub, blob = data
            try:
                names, rows = decode_chunk(blob)
            except Exception as e:  # noqa: BLE001
                print(f"{p_}: chunk skipped: {e}", file=sys.stderr)
                continue
            ts_idx = names.index("start") if "start" in names else 0

            if args.gaps:
                for r in rows:
                    ts = r[ts_idx]
                    if (lo and ts < lo) or (hi and ts >= hi):
                        continue
                    stamps.append(ts)
                continue

            idxs = [
                i for i, n in enumerate(names) if (not keep) or keep.search(n)
            ]
            kept = [names[i] for i in idxs]
            for n in kept:
                if n not in seen:
                    seen.add(n)
                    union.append(n)
            for r in rows:
                ts = r[ts_idx]
                if (lo and ts < lo) or (hi and ts >= hi):
                    continue
                per_chunk.append((ts, {kept[k]: r[i] for k, i in enumerate(idxs)}))

    if args.gaps:
        stamps.sort()
        print(f"samples={len(stamps)}")
        if stamps:
            print(f"first={ms_to_iso(stamps[0])} last={ms_to_iso(stamps[-1])}")
        prev = None
        for ts in stamps:
            if prev is not None:
                d = (ts - prev) / 1000.0
                if abs(d - 1.0) > 0.25:
                    print(f"  gap {d:7.2f}s  {ms_to_iso(prev)} -> {ms_to_iso(ts)}")
            prev = ts
        return

    if not per_chunk:
        print("no samples in range", file=sys.stderr)
        sys.exit(1)

    per_chunk.sort(key=lambda x: x[0])
    fh = open(args.out, "w", newline="") if args.out else sys.stdout
    w = csv.writer(fh)
    w.writerow(["ts_iso"] + union)
    for ts, d in per_chunk:
        w.writerow([ms_to_iso(ts)] + [d.get(n, "") for n in union])
    if args.out:
        fh.close()
        print(f"{len(per_chunk)} samples x {len(union)} columns -> {args.out}")


if __name__ == "__main__":
    main()
