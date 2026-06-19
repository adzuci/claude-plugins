"""OAuth authentication for HVO shadow booking.

Handles the one-time browser sign-in flow and token refresh.
Token cached at ~/.config/hvo-shadow/token.json.
Scopes: Calendar (read/write own calendar) + Sheets (read/write booking sheet).
"""

from __future__ import annotations

import json
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
]

CONFIG_DIR = Path.home() / ".config" / "hvo-shadow"
TOKEN_PATH = CONFIG_DIR / "token.json"

# Secret is never bundled in the repo — users place it at this path.
# Obtain it from the Apollo GCP project (data-platform-stg) OAuth credentials page.
SECRET_PATH = CONFIG_DIR / "client_secret.json"

_SECRET_INSTRUCTIONS = """
OAuth client secret not found at {path}

To set up:
  1. Download client_secret.json from 1Password:
     https://share.1password.com/s#S72iwphVK0aTnq_mqaicCQlKUUKnAS_dE81eZaHxzWU
  2. Save it to: {path}
  3. Re-run this command
""".strip()


def get_credentials():
    """Return valid Google credentials, running the browser flow if needed."""
    google_auth_oauthlib = __import__("google_auth_oauthlib.flow", fromlist=["InstalledAppFlow"])
    google_oauth2 = __import__("google.oauth2.credentials", fromlist=["Credentials"])
    google_auth_transport = __import__("google.auth.transport.requests", fromlist=["Request"])

    InstalledAppFlow = google_auth_oauthlib.InstalledAppFlow
    Credentials = google_oauth2.Credentials
    Request = google_auth_transport.Request

    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRET_PATH.exists():
                raise FileNotFoundError(_SECRET_INSTRUCTIONS.format(path=SECRET_PATH))
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return creds


def get_user_email(creds) -> str:
    """Return the authenticated user's email address."""
    token_data = json.loads(TOKEN_PATH.read_text()) if TOKEN_PATH.exists() else {}

    # Try id_token JWT payload first (present when openid scope was granted)
    if "id_token" in token_data:
        import base64
        payload_b64 = token_data["id_token"].split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        email = payload.get("email")
        if email:
            return email

    # Check token's account field (set by some OAuth flows)
    account = token_data.get("account", "")
    if "@" in account:
        return account

    # Reliable fallback: primary calendar id == user email
    googleapiclient = __import__("googleapiclient.discovery", fromlist=["build"])
    cal = googleapiclient.build("calendar", "v3", credentials=creds)
    primary = cal.calendars().get(calendarId="primary").execute()
    return primary.get("id", "unknown@apollo.io")
