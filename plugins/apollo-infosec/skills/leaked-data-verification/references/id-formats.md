# Record ID Formats

What each system Apollo runs actually emits, and what disqualifies a value.

## MongoDB — Apollo internal identifiers

Apollo's application data is Mongoid/BSON. Internal ids are **ObjectIds**.

| Property | Value |
| --- | --- |
| Shape | 24 lowercase hexadecimal characters |
| Prefix | None. No `cnt_`, `per_`, or similar |
| Structure | 4-byte timestamp, 5-byte random per-process value, 3-byte counter |
| Example | `694375d2ea31700011157c39` |
| Regex | `^[0-9a-f]{24}$` |

Disqualifying:

- Any character outside `[0-9a-f]` — uppercase hex included
- Length other than 24
- A namespace prefix
- Sequential values across rows. Real ObjectIds only look sequential when
  created in the same second by the same process
- A decoded timestamp outside the plausible life of the data

The leading 8 hex characters are a Unix timestamp. `check_id_formats.py`
decodes it.

## Salesforce

| Property | Value |
| --- | --- |
| Shape | 15 characters (case-sensitive) or 18 (case-insensitive) |
| Structure | 3-char object prefix, 2-char pod, 1 reserved, 9 unique |
| 18-char form | 15 chars plus a 3-character checksum |
| Example | `0015000000WWD2aAAH` |

Object key prefixes:

| Prefix | Object |
| --- | --- |
| `001` | Account |
| `003` | Contact |
| `005` | User |
| `006` | Opportunity |
| `00Q` | Lead |
| `500` | Case |
| `701` | Campaign |

Two checks, not one:

1. **Checksum.** For an 18-character id the trailing three characters must
   agree with the first 15. Each group of five characters contributes five
   bits, least significant first, set when the character is an uppercase
   letter; each 5-bit value indexes `ABCDEFGHIJKLMNOPQRSTUVWXYZ012345`.
1. **Prefix versus claimed entity.** A structurally valid Contact id sitting
   in a column labelled as an Account is a mismatch worth reporting.

APIs generally return the 18-character form, so a file of exclusively
15-character ids is worth a question.

## Snowflake

**Snowflake has no row-ID format.** It is a warehouse, not an OLTP store. Row
identity comes from whatever the pipeline generates: sequence-backed surrogate
keys, hashes of business keys, or source-system ids carried through.

The practical consequence: a column claiming Snowflake provenance that holds a
uniform, self-consistent synthetic identifier is a tell in itself. A genuine
warehouse export carries the *source systems'* native id formats, because that
is what the join key is.

Snowflake's own identifiers are query IDs, which are UUIDv4.

## Elasticsearch

Document `_id` is whatever the indexer set. Where Apollo indexes from Mongo,
expect the ObjectId to be carried through, so the Mongo rules above apply.
Where documents are composed, the id scheme is index-specific — confirm with
the owning team rather than assuming.

## Verify before relying on this

| Field | Value |
| --- | --- |
| Source | Apollo application code (Mongoid), Salesforce platform documentation |
| Verified | 2026-08-12 |

Formats change rarely, but the Salesforce prefix table grows as objects are
added. Confirm an unfamiliar prefix rather than treating it as invalid.
