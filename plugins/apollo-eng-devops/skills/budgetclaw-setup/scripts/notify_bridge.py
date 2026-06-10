#!/usr/bin/env python3
"""Loopback ntfy-to-macOS notification bridge for budgetclaw.

budgetclaw re-fires a warn on every event while over cap. This bridge coalesces
those POSTs into at most one popup per distinct title per cooldown window.
Suppressed POSTs still return 200 so budgetclaw remains happy.
"""

import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8410
COOLDOWN_SECONDS = 1800

# launchd runs with a bare PATH, so do not rely on `brew --prefix` or
# shutil.which at runtime. These two locations cover Apple Silicon and Intel.
TERMINAL_NOTIFIER = next(
    (
        path
        for path in (
            "/opt/homebrew/bin/terminal-notifier",
            "/usr/local/bin/terminal-notifier",
        )
        if os.path.exists(path)
    ),
    "/opt/homebrew/bin/terminal-notifier",
)

_last_sent = {}


def notify(title: str, message: str) -> None:
    now = time.monotonic()
    last = _last_sent.get(title)
    if last is not None and now - last < COOLDOWN_SECONDS:
        return

    _last_sent[title] = now
    subprocess.run(
        [
            TERMINAL_NOTIFIER,
            "-title",
            title or "budgetclaw",
            "-message",
            message or "(no message)",
            "-sound",
            "default",
            "-group",
            "budgetclaw",
            "-sender",
            "com.apple.Terminal",
        ],
        check=False,
    )


class Handler(BaseHTTPRequestHandler):
    def _ok(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"id":"local","event":"message"}')

    def do_GET(self) -> None:
        self._ok()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length).decode("utf-8", "replace") if length else ""
        title = self.headers.get("Title") or self.headers.get("X-Title") or "budgetclaw"
        notify(title, body)
        self._ok()

    def log_message(self, *args) -> None:
        pass


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
