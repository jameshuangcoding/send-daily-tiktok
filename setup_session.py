"""
One-time local setup script.

Launches a headed browser so you can log into TikTok manually.
After you close the browser, it saves the session and prints
a base64-encoded string to paste into the TIKTOK_SESSION GitHub Secret.
"""

import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

SESSION_FILE = Path("session_state.json")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://www.tiktok.com/login")

        print("\n=== TikTok Session Setup ===")
        print("1. Log into TikTok in the browser window that just opened.")
        print("2. Once you're fully logged in and see your feed, come back here.")
        input("\nPress Enter when you're logged in...")

        # Save session state
        storage = context.storage_state()
        SESSION_FILE.write_text(json.dumps(storage))
        print(f"\nSession saved to {SESSION_FILE}")

        browser.close()

    # Encode for GitHub Secret
    raw = SESSION_FILE.read_bytes()
    encoded = base64.b64encode(raw).decode()

    print("\n=== GitHub Secret ===")
    print("Create a repository secret named TIKTOK_SESSION with this value:\n")
    print(encoded)
    print("\nGo to: Settings → Secrets and variables → Actions → New repository secret")


if __name__ == "__main__":
    main()
