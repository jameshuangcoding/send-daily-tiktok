"""
Daily TikTok streak sender.

Sends a TikTok video URL as a DM to a friend via Playwright browser automation.
Designed to run in GitHub Actions on a daily cron schedule.
"""

import base64
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import pytz
from playwright.sync_api import sync_playwright

CONFIG_FILE = Path("config.json")
STATE_FILE = Path("streak_state.json")
SESSION_FILE = Path("session_state.json")


def load_config():
    return json.loads(CONFIG_FILE.read_text())


def load_state():
    return json.loads(STATE_FILE.read_text())


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def today_str(timezone):
    tz = pytz.timezone(timezone)
    return datetime.now(tz).strftime("%Y-%m-%d")


def pick_video_url(config, state):
    urls = config["video_urls"]
    last_url = state.get("last_video_url")

    # Avoid repeating the last URL if there are multiple options
    if last_url and len(urls) > 1:
        candidates = [u for u in urls if u != last_url]
    else:
        candidates = urls

    return random.choice(candidates)


def restore_session():
    """Decode TIKTOK_SESSION env var to session_state.json."""
    encoded = os.environ.get("TIKTOK_SESSION")
    if not encoded:
        # Fall back to local file (for local testing)
        if SESSION_FILE.exists():
            return
        print("ERROR: TIKTOK_SESSION env var not set and no local session_state.json found.")
        sys.exit(1)

    decoded = base64.b64decode(encoded)
    SESSION_FILE.write_bytes(decoded)


def check_login(page):
    """Check if we're on a login page (session expired)."""
    if "/login" in page.url:
        print("ERROR: Session expired. Re-run setup_session.py and update the TIKTOK_SESSION GitHub Secret.")
        sys.exit(1)


def send_message(config, video_url):
    """Automate sending a DM via Playwright."""
    friend = config["friend_username"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(SESSION_FILE))
        page = context.new_page()

        # Navigate to friend's profile
        profile_url = f"https://www.tiktok.com/@{friend}"
        print(f"Navigating to {profile_url}")
        page.goto(profile_url, wait_until="networkidle")
        check_login(page)

        # Click the message/DM icon on their profile
        # TikTok profile pages have a message icon button
        message_btn = page.locator('[data-e2e="message-icon"]').or_(
            page.locator('a[href*="/messages"]')
        ).or_(
            page.get_by_role("link", name="Messages")
        )
        message_btn.first.click(timeout=10000)
        print("Opened messages")

        # Wait for the chat/DM interface to load
        page.wait_for_url("**/messages**", timeout=15000)
        check_login(page)

        # Find the message input and type the video URL
        msg_input = page.locator('[data-e2e="message-input"]').or_(
            page.get_by_placeholder("Send a message...")
        ).or_(
            page.locator('[contenteditable="true"]')
        )
        msg_input.first.click(timeout=10000)
        msg_input.first.fill(video_url)
        print(f"Typed message: {video_url}")

        # Send the message (Enter key)
        msg_input.first.press("Enter")
        print("Sent message")

        # Brief wait to confirm message appears
        page.wait_for_timeout(3000)

        # Verify the message was sent by checking it appears in chat
        sent = page.locator(f'text="{video_url}"').or_(
            page.locator(f'[data-e2e="chat-message"]').filter(has_text=video_url)
        )
        if sent.first.is_visible(timeout=5000):
            print("Message verified in chat")
        else:
            print("WARNING: Could not verify message in chat, but send was attempted")

        browser.close()


def main():
    config = load_config()
    state = load_state()
    today = today_str(config["timezone"])

    # Idempotency check
    if state.get("last_sent_date") == today:
        print(f"Already sent today ({today}). Exiting.")
        return

    restore_session()

    video_url = pick_video_url(config, state)
    print(f"Selected video: {video_url}")

    send_message(config, video_url)

    # Update state on success
    state["last_sent_date"] = today
    state["last_video_url"] = video_url
    save_state(state)
    print(f"Streak state updated: sent on {today}")


if __name__ == "__main__":
    main()
