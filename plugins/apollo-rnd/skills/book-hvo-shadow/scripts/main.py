"""HVO Shadow Booking CLI.

Commands:
  auth              Force a fresh browser sign-in and cache the token.
  list              Show available shadow slots for all (or one) HVO member.
  book              Book a specific slot by index from the list output.

Usage:
  python main.py auth
  python main.py list
  python main.py list --member "Ana Mejia"
  python main.py book --index 3
"""

from __future__ import annotations

import argparse
import sys


def cmd_auth(_args: argparse.Namespace) -> None:
    from auth import TOKEN_PATH, get_credentials, get_user_email

    TOKEN_PATH.unlink(missing_ok=True)
    creds = get_credentials()
    email = get_user_email(creds)
    print(f"Authenticated as: {email}")
    print(f"Token cached at: {TOKEN_PATH}")


def cmd_list(args: argparse.Namespace) -> None:
    from auth import get_credentials
    from calendar_reader import fetch_slots, format_slot_label
    from members import all_calendar_emails, find_by_name, display_name_for

    creds = get_credentials()

    if args.member:
        result = find_by_name(args.member)
        if not result:
            print(f"No HVO member found matching '{args.member}'. Use their display name.")
            sys.exit(1)
        cal_email, _ = result
        emails = [cal_email]
    else:
        emails = all_calendar_emails()

    date = getattr(args, "date", None)
    time_from = getattr(args, "time_from", None)
    time_to = getattr(args, "time_to", None)

    if date:
        print(f"Fetching slots for {date} (Mexico City time)...\n")
    else:
        print("Fetching upcoming 'Exclusive Customer Onboarding' slots...\n")
    slots = fetch_slots(creds, emails, display_name_for, date=date)

    import json

    def _clear_cache():
        """Invalidate the slot cache so stale `book --index` calls are rejected."""
        cache_path = _slot_cache_path()
        with open(cache_path, "w") as f:
            json.dump([], f)

    if not slots:
        _clear_cache()
        window = f"on {date}" if date else "in the next 14 days"
        print(f"No available slots found {window}.")
        print("This usually means HVO calendars aren't shared with your account.")
        print("Contact your HVO program manager to enable calendar visibility.")
        return

    # Apply time range filter if provided
    from calendar_reader import filter_by_time_range
    if time_from or time_to:
        slots = filter_by_time_range(slots, time_from, time_to)
        if not slots:
            _clear_cache()
            print(f"No slots found between {time_from or '00:00'} and {time_to or '23:59'} Mexico City time.")
            return

    # If still too many, tell the user to narrow the window
    TOO_MANY = 25
    if len(slots) > TOO_MANY:
        _clear_cache()
        print(f"Too many slots to print here ({len(slots)} found).")
        print("Please choose a time window you want (Mexico City time).")
        print("Note: HVO sessions start at 8:00 AM Mexico City time.")
        print("Example: --from 08:00 --to 10:00")
        return

    # Cache slots for `book --index N`
    cache_path = _slot_cache_path()
    with open(cache_path, "w") as f:
        json.dump(slots, f, indent=2)

    print(f"{'#':<4} {'Slot'}")
    print("-" * 60)
    for i, slot in enumerate(slots, start=1):
        label = format_slot_label(slot)
        meet = f"  [{slot['meet_link']}]" if slot.get("meet_link") else ""
        print(f"{i:<4} {label}{meet}")

    print(f"\nTo book, run: python main.py book --index <NUMBER>")


def cmd_book(args: argparse.Namespace) -> None:
    import json

    from auth import get_credentials, get_user_email

    cache_path = _slot_cache_path()
    if not cache_path.exists():
        print("No slot list cached. Run `python main.py list` first.")
        sys.exit(1)

    with open(cache_path) as f:
        slots = json.load(f)

    idx = args.index - 1
    if idx < 0 or idx >= len(slots):
        print(f"Invalid index {args.index}. Valid range: 1–{len(slots)}.")
        sys.exit(1)

    slot = slots[idx]

    from calendar_reader import format_slot_label
    print(f"Booking: {format_slot_label(slot)}")
    if not args.yes:
        confirm = input("Confirm? [y/N] ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Cancelled.")
            return

    creds = get_credentials()
    booked_by = get_user_email(creds)

    googleapiclient = __import__("googleapiclient.discovery", fromlist=["build"])
    sheets_service = googleapiclient.build("sheets", "v4", credentials=creds)
    cal_service = googleapiclient.build("calendar", "v3", credentials=creds)

    from sheet_manager import append_booking, store_cal_event_id
    result = append_booking(sheets_service, slot, booked_by)

    if not result["success"]:
        print(f"Booking failed: {result['message']}")
        sys.exit(1)

    print(f"\n{result['message']}")

    event_id = _create_shadow_event(cal_service, slot, booked_by)
    if event_id and result.get("row_index"):
        store_cal_event_id(sheets_service, result["row_index"], event_id)

    if result.get("meet_link"):
        print(f"Meet link: {result['meet_link']}")


def cmd_cancel(args: argparse.Namespace) -> None:
    from auth import get_credentials, get_user_email
    from sheet_manager import find_my_bookings, cancel_booking, read_all_rows

    creds = get_credentials()
    booked_by = get_user_email(creds)

    googleapiclient = __import__("googleapiclient.discovery", fromlist=["build"])
    sheets_service = googleapiclient.build("sheets", "v4", credentials=creds)

    rows = read_all_rows(sheets_service)
    bookings = find_my_bookings(rows, booked_by)

    if not bookings:
        print(f"No confirmed bookings found for {booked_by}.")
        return

    print(f"Your confirmed bookings ({booked_by}):\n")
    for i, b in enumerate(bookings, start=1):
        print(f"  {i}. {b['host']} on {b['date']} at {b['time']}")

    print()
    if getattr(args, "index", None):
        idx = args.index - 1
        if idx < 0 or idx >= len(bookings):
            print(f"Invalid index {args.index}. Valid range: 1–{len(bookings)}.")
            sys.exit(1)
    else:
        while True:
            raw = input("Enter booking number to cancel (or 'q' to quit): ").strip()
            if raw.lower() in ("q", "quit"):
                print("Cancelled.")
                return
            if raw.isdigit() and 1 <= int(raw) <= len(bookings):
                idx = int(raw) - 1
                break
            print(f"  Please enter a number between 1 and {len(bookings)}.")

    b = bookings[idx]
    print(f"\nCancelling: {b['host']} on {b['date']} at {b['time']}")
    if not getattr(args, "yes", False):
        confirm = input("Confirm cancellation? [y/N] ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Cancelled.")
            return

    # Delete the [Shadow] calendar event if one was stored
    event_id = b.get("event_id", "")
    if event_id:
        try:
            cal_service = googleapiclient.build("calendar", "v3", credentials=creds)
            cal_service.events().delete(calendarId="primary", eventId=event_id).execute()
            print("Calendar event deleted.")
        except Exception as e:
            print(f"Warning: could not delete calendar event ({e}). Remove it manually.")

    cancel_booking(sheets_service, b["row_index"])
    print("Booking cancelled and slot freed.")


def _create_shadow_event(cal_service, slot: dict, booked_by: str) -> str:
    """Drop a shadow calendar event on the booker's primary calendar. Returns the event ID."""
    meet_line = f"\nMeet link: {slot['meet_link']}" if slot.get("meet_link") else ""
    body = {
        "summary": f"[Shadow] HVO Session with {slot['member_name']}",
        "description": (
            f"Shadow session — observing {slot['member_name']}'s Exclusive Customer Onboarding call."
            f"{meet_line}\n\n"
            "Note: You are shadowing this call. Do not unmute unless invited to."
        ),
        "start": {"dateTime": slot["start"]},
        "end": {"dateTime": slot["end"]},
    }

    event = cal_service.events().insert(calendarId="primary", body=body).execute()
    print(f"Calendar event created: {event.get('htmlLink', '(no link)')}")
    return event.get("id", "")


def cmd_run(args: argparse.Namespace) -> None:
    """Interactive wizard: auth → list → pick → book in one session."""
    from auth import TOKEN_PATH, get_credentials, get_user_email
    from calendar_reader import fetch_slots, format_slot_label
    from members import all_calendar_emails, find_by_name

    # --- Auth (silent if token already cached) ---
    print("Checking Google authentication...")
    creds = get_credentials()
    booked_by = get_user_email(creds)
    print(f"Signed in as: {booked_by}\n")

    # --- Fetch slots ---
    member_arg = getattr(args, "member", None)
    if member_arg:
        result = find_by_name(member_arg)
        if not result:
            print(f"No HVO member found matching '{member_arg}'.")
            sys.exit(1)
        cal_email, _ = result
        emails = [cal_email]
    else:
        emails = all_calendar_emails()

    from members import display_name_for
    print("Fetching upcoming 'Exclusive Customer Onboarding' slots...\n")
    slots = fetch_slots(creds, emails, display_name_for)

    if not slots:
        print("No available slots found in the next 14 days.")
        print("This usually means HVO calendars aren't shared with your account.")
        print("Contact your HVO program manager to enable calendar visibility.")
        return

    # Cache for `book --index` fallback
    import json
    with open(_slot_cache_path(), "w") as f:
        json.dump(slots, f, indent=2)

    # --- Display ---
    print(f"{'#':<4} {'Slot'}")
    print("-" * 64)
    for i, slot in enumerate(slots, start=1):
        label = format_slot_label(slot)
        meet = "  [Meet link available]" if slot.get("meet_link") else ""
        print(f"{i:<4} {label}{meet}")

    # --- Pick ---
    print()
    while True:
        raw = input("Enter slot number to book (or 'q' to quit): ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            print("Cancelled.")
            return
        if raw.isdigit() and 1 <= int(raw) <= len(slots):
            idx = int(raw) - 1
            break
        print(f"  Please enter a number between 1 and {len(slots)}.")

    slot = slots[idx]
    print(f"\nYou selected: {format_slot_label(slot)}")
    confirm = input("Confirm booking? [y/N] ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Cancelled.")
        return

    # --- Book ---
    googleapiclient = __import__("googleapiclient.discovery", fromlist=["build"])
    sheets_service = googleapiclient.build("sheets", "v4", credentials=creds)
    cal_service = googleapiclient.build("calendar", "v3", credentials=creds)

    from sheet_manager import append_booking, store_cal_event_id
    result = append_booking(sheets_service, slot, booked_by)

    if not result["success"]:
        print(f"\nBooking failed: {result['message']}")
        sys.exit(1)

    print(f"\n{result['message']}")

    event_id = _create_shadow_event(cal_service, slot, booked_by)
    if event_id and result.get("row_index"):
        store_cal_event_id(sheets_service, result["row_index"], event_id)

    if result.get("meet_link"):
        print(f"Meet link: {result['meet_link']}")


def _slot_cache_path():
    from pathlib import Path
    cache_dir = Path.home() / ".config" / "hvo-shadow"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "slots_cache.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="hvo-shadow",
        description="Book a shadow slot on an HVO team member's customer call.",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    run_p = sub.add_parser("run", help="Interactive wizard: auth → list → book in one go.")
    run_p.add_argument("--member", metavar="NAME", help="Filter to a specific HVO member.")

    sub.add_parser("auth", help="Sign in with your @apollo.io Google account.")

    list_p = sub.add_parser("list", help="List available shadow slots.")
    list_p.add_argument("--member", metavar="NAME", help="Filter to a specific HVO member.")
    list_p.add_argument("--date", metavar="YYYY-MM-DD", help="Date to fetch slots for (Mexico City time).")
    list_p.add_argument("--from", dest="time_from", metavar="HH:MM", help="Start of time window (Mexico City time, 24h).")
    list_p.add_argument("--to", dest="time_to", metavar="HH:MM", help="End of time window (Mexico City time, 24h).")

    book_p = sub.add_parser("book", help="Book a slot by index from the list output.")
    book_p.add_argument("--index", type=int, required=True, metavar="N", help="Slot number from `list`.")
    book_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")

    cancel_p = sub.add_parser("cancel", help="Cancel one of your confirmed bookings.")
    cancel_p.add_argument("--index", type=int, metavar="N", help="Booking number to cancel (from the displayed list).")
    cancel_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt.")

    args = parser.parse_args()
    # Default to `run` when no subcommand given
    command = args.command or "run"
    if command == "run" and not hasattr(args, "member"):
        args.member = None
    {"run": cmd_run, "auth": cmd_auth, "list": cmd_list, "book": cmd_book, "cancel": cmd_cancel}[command](args)


if __name__ == "__main__":
    main()
