# Reserved Values

Values that standards bodies reserve for documentation and testing. They cannot
appear in real customer data, so finding one proves fabrication outright.

Their absence proves nothing.

## Domains — RFC 2606 and RFC 6761

Reserved top-level domains, which can never be registered or resolve:

- `.example`
- `.test`
- `.invalid`
- `.localhost`

Reserved second-level domains:

- `example.com`
- `example.net`
- `example.org`

An address like `luca.costa@praxis-systems.example` is not a plausible
misspelling. `.example` is unregistrable by design.

Watch for near-misses that are *not* reserved and should not be flagged:
`exampleco.com`, `mytest.com`, `example.io`.

## Phone numbers — NANP fictional range

Only **555-0100 through 555-0199** is reserved for fictional use. The full
555 exchange is not: 555-1212 is directory assistance, and other 555 numbers
are assignable.

Flagging every 555 number produces false positives. `scan_reserved_values.py`
checks the line range, not just the exchange.

Numbers outside North America have their own reserved ranges — for example
Ofcom reserves several UK blocks including `020 7946 0xxx`. The scanner does
not currently check these; treat a sample of exclusively UK numbers as
unscanned rather than clean.

## IP addresses — RFC 5737

Documentation ranges:

- `192.0.2.0/24`
- `198.51.100.0/24`
- `203.0.113.0/24`

Also worth noting if present: `2001:db8::/32` for IPv6 documentation, and the
`.arpa` reserved namespaces.

## Other generated-data markers

Not standards-reserved, but strong signals in combination:

- Placeholder profile URLs — `linkedin.example/in/...`
- Names drawn from a small repeating pool across thousands of rows
- Street addresses that repeat a handful of city templates
- Sequential numeric suffixes inside otherwise human-looking values, such as
  `first.last.00001@`

Any one of these is weak on its own. Several together, across every column,
describe a generator rather than an export.

## Verify before relying on this

| Field | Value |
| --- | --- |
| Source | RFC 2606, RFC 5737, RFC 6761; NANP assignment rules |
| Verified | 2026-08-12 |
