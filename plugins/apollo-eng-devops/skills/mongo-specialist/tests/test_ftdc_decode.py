"""FTDC decode regressions.

Both bugs these cover were hit for real while decoding mongo-email-shard-16-b
during INCIDENT-34256, and both produce *plausible but wrong* numbers rather
than an error, which is what makes them worth pinning.
"""

from __future__ import annotations

import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

import ftdc_decode as f

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "ftdc_decode.py"
T0 = 1790778000000  # 2026-09-30T14:20:00Z


def _cstr(s: str) -> bytes:
    return s.encode() + b"\x00"


def _doc(items: list[bytes]) -> bytes:
    body = b"".join(items)
    return struct.pack("<i", len(body) + 5) + body + b"\x00"


def _i32(k, v):
    return b"\x10" + _cstr(k) + struct.pack("<i", v)


def _i64(k, v):
    return b"\x12" + _cstr(k) + struct.pack("<q", v)


def _date(k, v):
    return b"\x09" + _cstr(k) + struct.pack("<q", v)


def _ts(k, sec, inc):
    return b"\x11" + _cstr(k) + struct.pack("<II", inc, sec)


def _str(k, v):
    return b"\x02" + _cstr(k) + struct.pack("<i", len(v) + 1) + v.encode() + b"\x00"


def _bool(k, v):
    return b"\x08" + _cstr(k) + bytes([1 if v else 0])


def _sub(k, items):
    return b"\x03" + _cstr(k) + _doc(items)


def _varint(n: int) -> bytes:
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def _encode_deltas(columns: list[list[int]]) -> bytes:
    """Column-major varints with zero run-length encoding, as FTDC writes them."""
    flat: list[int] = []
    for c in columns:
        flat.extend(c)
    out = b""
    i = 0
    while i < len(flat):
        if flat[i] == 0:
            j = i
            while j < len(flat) and flat[j] == 0:
                j += 1
            out += _varint(0) + _varint(j - i - 1)
            i = j
        else:
            out += _varint(flat[i])
            i += 1
    return out


def _chunk(ref: bytes, nmetrics: int, columns: list[list[int]], override_nmetrics=None) -> bytes:
    nsamples = len(columns[0])
    payload = (
        ref
        + struct.pack("<II", override_nmetrics if override_nmetrics is not None else nmetrics, nsamples)
        + _encode_deltas(columns)
    )
    return struct.pack("<I", len(payload)) + zlib.compress(payload)


def _file_doc(chunk: bytes, ts: int) -> bytes:
    return _doc(
        [
            _date("_id", ts),
            _i32("type", 1),
            b"\x05" + _cstr("data") + struct.pack("<i", len(chunk)) + b"\x00" + chunk,
        ]
    )


def test_bson_timestamp_contributes_two_columns():
    """A Timestamp is seconds AND increment. Counting it once shifts every later column."""
    ref = _doc([_date("start", T0), _ts("opTime", 1000, 7), _i64("after", 42)])
    names, rows = f.decode_chunk(_chunk(ref, 4, [[1000], [1], [0], [0]]))

    assert names == ["start", "opTime", "opTime.inc", "after"]
    assert rows[1] == [T0 + 1000, 1001, 7, 42]


def test_non_numeric_bson_types_contribute_no_columns():
    ref = _doc([_date("start", T0), _str("host", "x"), _bool("ok", True), _sub("wt", [_i32("t", 5)])])
    names, _ = f.decode_chunk(_chunk(ref, 3, [[0], [0], [0]]))

    assert names == ["start", "ok", "wt.t"]


def test_zero_run_length_and_64_bit_wraparound():
    ref = _doc([_date("start", T0), _i64("ticks", 3)])
    # ticks decrements by one via unsigned wraparound; start advances 1s per sample
    names, rows = f.decode_chunk(_chunk(ref, 2, [[1000, 1000], [(1 << 64) - 1, (1 << 64) - 1]]))

    assert [r[names.index("ticks")] for r in rows] == [3, 2, 1]


def test_refuses_to_emit_when_header_count_disagrees_with_reference_doc():
    ref = _doc([_date("start", T0), _i64("a", 1)])
    with pytest.raises(ValueError, match="metric count mismatch"):
        f.decode_chunk(_chunk(ref, 2, [[0], [0]], override_nmetrics=5))


def test_columns_are_mapped_per_chunk_not_by_first_chunk_index(tmp_path):
    """Each chunk carries its own reference doc. Reusing chunk 1's indices silently
    misattributes chunk 2's values, or raises IndexError when chunk 2 is narrower."""
    ref_a = _doc([_date("start", T0), _i64("alpha", 10), _i64("beta", 20)])
    ref_b = _doc([_date("start", T0 + 2000), _i64("beta", 99)])  # narrower, reordered

    blob = _file_doc(_chunk(ref_a, 3, [[1000], [0], [0]]), T0)
    blob += _file_doc(_chunk(ref_b, 2, [[1000], [0]]), T0 + 2000)
    src = tmp_path / "metrics.test"
    src.write_bytes(blob)
    out = tmp_path / "o.csv"

    subprocess.run(
        [sys.executable, str(SCRIPT), str(src), "--grep", "beta", "--out", str(out)],
        check=True,
        capture_output=True,
    )
    lines = out.read_text().strip().splitlines()

    assert lines[0] == "ts_iso,beta"
    assert [ln.split(",")[1] for ln in lines[1:]] == ["20", "20", "99", "99"]


def test_gaps_reports_only_non_1s_intervals(tmp_path):
    ref = _doc([_date("start", T0)])
    # 1s, 1s, then a 7s jump: the mongo-email-shard-16-b FTDC stall signature
    blob = _file_doc(_chunk(ref, 1, [[1000, 1000, 7000]]), T0)
    src = tmp_path / "metrics.test"
    src.write_bytes(blob)

    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(src), "--gaps"], check=True, capture_output=True, text=True
    )

    assert "samples=4" in r.stdout
    assert r.stdout.count("gap") == 1
    assert "7.00s" in r.stdout
