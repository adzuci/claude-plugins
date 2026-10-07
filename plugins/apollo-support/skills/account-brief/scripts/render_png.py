#!/usr/bin/env python3
"""Rasterize an account-brief HTML file to PNG for inline Slack display.

Slack renders an attached PNG inline but shows raw HTML as unreadable text, so
the PNG is the artifact that actually reads well in a thread.

Tries each available renderer in order and reports which one worked. PNG is
best-effort by design: when no renderer is installed this exits non-zero with an
actionable reason so the caller can fall back to the HTML file plus the Slack
text summary instead of failing the whole brief.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 1600
CHROME_BINARIES = ("google-chrome", "chromium", "chromium-browser", "chrome")


class RenderError(RuntimeError):
    """No renderer could produce a PNG."""


def find_chrome() -> str | None:
    """Return the first Chrome-family binary on PATH, or None."""
    for name in CHROME_BINARIES:
        path = shutil.which(name)
        if path:
            return path
    return None


def render_with_playwright(html_path: Path, output_path: Path, width: int) -> str:
    """Full-page screenshot via Playwright. Best fidelity: captures the whole document.

    The viewport starts short on purpose. A full-page screenshot is at least as
    tall as the viewport, so a tall one pads a short brief with dead space.
    """
    from playwright.sync_api import sync_playwright  # imported lazily; optional dependency

    with sync_playwright() as play:
        browser = play.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": 600})
            page.goto(html_path.resolve().as_uri(), wait_until="load")
            page.screenshot(path=str(output_path), full_page=True)
        finally:
            browser.close()
    return "playwright"


def render_with_chrome(html_path: Path, output_path: Path, width: int, height: int) -> str:
    """Headless Chrome screenshot.

    Chrome captures the window, not the full document, so height is a fixed
    window size rather than the real content height. Pass --height when a long
    brief is cut off, or install Playwright for true full-page capture.
    """
    binary = find_chrome()
    if not binary:
        raise RenderError("no Chrome-family binary on PATH")

    with tempfile.TemporaryDirectory() as profile:
        result = subprocess.run(
            [
                binary,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                f"--user-data-dir={profile}",
                f"--window-size={width},{height}",
                f"--screenshot={output_path}",
                html_path.resolve().as_uri(),
            ],
            capture_output=True,
            text=True,
            # Chrome renders a brief in seconds. A longer wait means it is
            # wedged (sandboxed container, no display), so give up and let the
            # caller fall back rather than stalling the AM.
            timeout=60,
        )
    if not output_path.exists():
        detail = (result.stderr or result.stdout or "no output").strip().splitlines()
        raise RenderError(f"chrome produced no file: {detail[-1] if detail else 'unknown error'}")
    return f"chrome ({Path(binary).name})"


def render_png(
    html_path: Path,
    output_path: Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> tuple[bool, str]:
    """Render HTML to PNG using the first renderer that works.

    Returns (ok, detail). Never raises: a failed render is a degraded brief, not
    a crashed one. The caller attaches the HTML instead and says so in Slack.
    """
    if not html_path.exists():
        return False, f"html file not found: {html_path}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    attempts: list[str] = []

    for name, call in (
        ("playwright", lambda: render_with_playwright(html_path, output_path, width)),
        ("chrome", lambda: render_with_chrome(html_path, output_path, width, height)),
    ):
        try:
            used = call()
            return True, used
        except Exception as exc:  # noqa: BLE001 - any renderer failure falls through to the next
            attempts.append(f"{name}: {type(exc).__name__}: {exc}")

    return False, (
        "no PNG renderer available. Tried "
        + "; ".join(attempts)
        + ". Install Playwright (`pip install playwright && playwright install chromium`) "
        "or Chrome, then retry. Attach the HTML file instead and say the PNG could not be built."
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, help="Path to the rendered HTML brief.")
    parser.add_argument("--output", required=True, help="Path to write the PNG.")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help=f"Viewport width (default: {DEFAULT_WIDTH}).")
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Window height for the Chrome fallback (default: {DEFAULT_HEIGHT}).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    ok, detail = render_png(Path(args.html), Path(args.output), args.width, args.height)
    if ok:
        print(f"PNG saved to {args.output} (renderer: {detail})")
        return 0
    print(f"PNG not rendered: {detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
