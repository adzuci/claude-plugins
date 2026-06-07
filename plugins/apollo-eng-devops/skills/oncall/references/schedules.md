# DevOps + Platform PagerDuty schedules

The scripts resolve schedules **dynamically by name** (see `TEAM_PATTERNS` /
`ROLE_PATTERNS` in `scripts/lib.py`). This file is a human-readable cache + override:
fill in the real schedule names and IDs once you've confirmed them, so reviewers and
future on-calls don't have to re-derive the mapping.

## How to find the IDs

```bash
pd schedule:list
# or, for the raw API objects (id + name):
pd rest:get -e /schedules?limit=100
```

## Known schedules

> Fill these in from `pd schedule:list`. Leave a row blank if a team has no secondary.

| Team | Role | Schedule name | Schedule ID |
| --- | --- | --- | --- |
| DevOps | Primary | _TODO_ | _TODO_ |
| DevOps | Secondary | _TODO_ | _TODO_ |
| Platform | Primary | _TODO_ | _TODO_ |
| Platform | Secondary | _TODO_ | _TODO_ |

## Name-matching notes

- `classify_team` matches `devops` / `dev ops` / `sre` / `infra` → **devops**, and
  `platform` / `plat` → **platform**.
- `classify_role` treats `secondary` / `backup` / `shadow` / `2nd` as **secondary**;
  everything else defaults to **primary**.
- If a real schedule name doesn't match (e.g. a codename), extend the patterns in
  `scripts/lib.py` rather than hard-coding IDs into the scripts.
