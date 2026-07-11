#!/usr/bin/env python3
"""Upload a local image to Notion using the File Upload API.

Requires:
  pip install requests
  NOTION_PAK env var — Notion Personal API Key (starts with ntn_)

Usage:
  python3 upload_notion_image.py <image_path>
  python3 upload_notion_image.py <image_path> --page-id <notion_page_id>

Without --page-id: prints JSON with file_upload_id and image_block.
With --page-id: also appends the image to the specified Notion page.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"
REQUEST_TIMEOUT = 30  # seconds; uploads of small screenshots comfortably fit


def get_pak() -> str:
    pak = os.environ.get("NOTION_PAK", "")
    if not pak:
        print("Error: NOTION_PAK env var not set (expected ntn_... key).", file=sys.stderr)
        sys.exit(1)
    return pak


def _auth_headers(pak: str) -> dict:
    return {
        "Authorization": f"Bearer {pak}",
        "Notion-Version": NOTION_VERSION,
        "accept": "application/json",
    }


def upload_image(image_path: str, pak: str) -> dict:
    path = os.path.abspath(image_path)
    if not os.path.isfile(path):
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(path)
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or "application/octet-stream"

    # Step 1: Create file upload object
    resp = requests.post(
        f"{NOTION_API_BASE}/file_uploads",
        json={"filename": filename, "content_type": mime_type},
        headers={**_auth_headers(pak), "content-type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        print(f"Create file_upload failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    file_upload_id = resp.json()["id"]

    # Step 2: Upload file content
    with open(path, "rb") as f:
        resp = requests.post(
            f"{NOTION_API_BASE}/file_uploads/{file_upload_id}/send",
            headers=_auth_headers(pak),
            files={"file": (filename, f, mime_type)},
            timeout=REQUEST_TIMEOUT,
        )
    if resp.status_code != 200:
        print(f"File send failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    image_block = {
        "object": "block",
        "type": "image",
        "image": {
            "type": "file_upload",
            "file_upload": {"id": file_upload_id},
        },
    }
    return {"file_upload_id": file_upload_id, "filename": filename, "image_block": image_block}


def append_to_page(page_id: str, image_block: dict, pak: str) -> None:
    resp = requests.patch(
        f"{NOTION_API_BASE}/blocks/{page_id}/children",
        json={"children": [image_block]},
        headers={**_auth_headers(pak), "content-type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        print(f"Append block failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a local image to Notion.")
    parser.add_argument("image_path", help="Path to a local image file (png, jpg, gif, etc.).")
    parser.add_argument(
        "--page-id",
        help="Notion page ID to append the image block to after uploading.",
    )
    args = parser.parse_args()

    pak = get_pak()
    result = upload_image(args.image_path, pak)

    if args.page_id:
        append_to_page(args.page_id, result["image_block"], pak)
        result["appended_to_page"] = args.page_id

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
