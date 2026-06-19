---
name: book-hvo-shadow
description: Book a shadow slot on an HVO team member's Exclusive Customer Onboarding call.
argument-hint: "[optional: HVO member name to filter by]"
disable-model-invocation: true
---

# HVO Shadow Booking

You help R&D members book a shadow slot to observe an HVO team member's customer onboarding
call. One shadow per call is enforced.

## Setup (first run only)

**Step A — Place the OAuth client secret**

The credential file is not bundled in the repo. Get it once from 1Password:

1. Download `client_secret.json` from:
   https://share.1password.com/s#S72iwphVK0aTnq_mqaicCQlKUUKnAS_dE81eZaHxzWU
2. Save it to `~/.config/hvo-shadow/client_secret.json`

**Step B — Install Python dependencies**

```bash
VENV="$HOME/.config/hvo-shadow/venv"
SCRIPTS="${CLAUDE_PLUGIN_ROOT}/skills/book-hvo-shadow/scripts"

if [ ! -d "$VENV" ]; then
  echo "Setting up HVO shadow environment (one-time)..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$SCRIPTS/requirements.txt"
fi

PYTHON="$VENV/bin/python"
```

## Step 1 — Ask for a date and time range

Ask the user both questions upfront:

> "Which date are you looking to shadow? (e.g. June 25)"
> "What time range works for you? Note: HVO sessions start at 8:00 AM Mexico City time."

Convert the date to YYYY-MM-DD. Convert the time range to HH:MM–HH:MM (24h, Mexico City time).
Both are required — do not skip.

## Step 2 — List slots for that date and time window

```bash
$PYTHON "$SCRIPTS/main.py" list --date "$DATE" --from "$TIME_FROM" --to "$TIME_TO"
```

If the script responds with "Too many slots to print here", the time window is still too broad —
ask the user to narrow it and re-run with a tighter `--from`/`--to` range.

If no slots appear, explain that those HVO members' calendars may not be shared with your account.

To also filter by a specific HVO member:

```bash
$PYTHON "$SCRIPTS/main.py" list --date "$DATE" --from "$TIME_FROM" --to "$TIME_TO" --member "$MEMBER_NAME"
```

## Step 3 — Book the chosen slot

Ask the user to pick a number from the list, confirm their choice, then run:

```bash
$PYTHON "$SCRIPTS/main.py" book --index <N> --yes
```

This will:

1. Check the booking sheet for conflicts.
2. Write a row to the shared Google Sheet with an optimistic lock.
3. Create a `[Shadow]` event on the user's own Google Calendar.
4. Print the Meet link if available.

If the slot is already taken, re-run `list` with the same date and time window and offer the
remaining options.

## Notes

- The skill does **not** add the booker as an attendee to the HVO member's event — the customer
  does not see the shadow. The shadow event is on the booker's calendar only.
- One shadow per call is enforced.
- To cancel: delete the `[Shadow]` calendar event and notify the HVO member directly.
