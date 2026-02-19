"""
One-time local setup script.

Converts a raw Cookie header string (from Chrome DevTools) into a
Playwright session file, then prints the base64 value for GitHub Secrets.

Steps:
  1. Go to https://www.tiktok.com in Chrome (logged in)
  2. Open DevTools → Network tab
  3. Click any request to tiktok.com
  4. Find Request Headers → Cookie → copy the entire value
  5. Paste it into a file called cookies.txt in this directory
  6. Run: python setup_session.py
"""

import base64
import json
from pathlib import Path

SESSION_FILE = Path("session_state.json")
COOKIES_FILE = Path("cookies.txt")


def parse_cookie_string(cookie_str: str) -> list:
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        name, _, value = part.partition("=")
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".tiktok.com",
            "path": "/",
            "expires": -1,
            "httpOnly": False,
            "secure": True,
            "sameSite": "None",
        })
    return cookies


def main():
    if not COOKIES_FILE.exists():
        print(f"ERROR: {COOKIES_FILE} not found.")
        print("Paste your Chrome DevTools Cookie header value into cookies.txt and re-run.")
        return

    cookie_str = COOKIES_FILE.read_text().strip()
    cookies = parse_cookie_string(cookie_str)
    storage_state = {"cookies": cookies, "origins": []}

    SESSION_FILE.write_text(json.dumps(storage_state, indent=2))
    print(f"Session saved to {SESSION_FILE} ({len(cookies)} cookies)")

    raw = SESSION_FILE.read_bytes()
    encoded = base64.b64encode(raw).decode()

    print("\n=== GitHub Secret ===")
    print("Create a repository secret named TIKTOK_SESSION with this value:\n")
    print(encoded)
    print("\nGo to: Settings → Secrets and variables → Actions → New repository secret")


if __name__ == "__main__":
    main()
