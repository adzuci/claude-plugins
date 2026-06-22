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

**Step A — Install Python dependencies**

> **Credentials are fetched automatically** on first run from the Apollo GCP token server
> (requires `gcloud auth login` with your `@apollo.io` account). No manual secret download needed.

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

All HVO sessions run between **8:00 AM and 4:00 PM Mexico City time** (UTC-6). Before asking,
convert this window to the user's local timezone and present it to them so they know what's
available. For example:
- IST (UTC+5:30): 7:30 PM – 1:30 AM next day
- PST (UTC-8): 6:00 AM – 2:00 PM
- EST (UTC-5): 9:00 AM – 5:00 PM
- CET (UTC+1): 3:00 PM – 11:00 PM

Ask the user both questions upfront, always framing the time range in **their local timezone**:

> "Which date are you looking to shadow? (e.g. June 25)"
> "What time range works for you? Sessions are available between [8 AM–4 PM Mexico City time, which is HH:MM–HH:MM in your timezone]."

If the user picks a time outside the 8 AM–4 PM Mexico City window, let them know no sessions
run at that time and ask them to pick within the available window (shown in their timezone).

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

Once booked, always remind the user:

> "Please give the HVO host a heads-up that you'll be shadowing their session. You can reach
> out to [HVO member name] directly on Slack to let them know."

## Notes

- The skill does **not** add the booker as an attendee to the HVO member's event — the customer
  does not see the shadow. The shadow event is on the booker's calendar only.
- One shadow per call is enforced.
- To cancel: delete the `[Shadow]` calendar event and notify the HVO member directly.
