# send-daily-tiktok

Automatically sends a TikTok video DM to a friend once per day to maintain a messaging streak. Runs on GitHub Actions — no laptop needed after initial setup.

## How it works

A GitHub Actions cron job runs daily at 9 AM ET. It restores a TikTok browser session from a GitHub Secret, opens the messages page with Playwright, finds the friend's conversation, and sends a video URL. After a successful send, it commits the updated `streak_state.json` to prevent duplicate sends.

## Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Edit `config.json`:

```json
{
  "friend_username": "INSERT_USERNAME_HERE",
  "friend_display_name": "INSERT_DISPLAY_NAME_HERE",
  "timezone": "America/New_York",
  "video_urls": [
    "https://www.tiktok.com/@someone/video/123"
  ]
}
```

- `friend_username` — TikTok handle (used for profile URL)
- `friend_display_name` — name as it appears in your messages inbox
- `video_urls` — list of videos to cycle through (avoids repeating the last one)

### 3. Capture your session

1. Log into TikTok in Chrome
2. Open DevTools → Network tab → click any tiktok.com request → copy the `Cookie` request header value
3. Paste it into a file called `cookies.txt` in the project directory
4. Run:

```bash
python setup_session.py
```

This generates `session_state.json` and prints a base64 string.

### 4. Add the GitHub Secret

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

- Name: `TIKTOK_SESSION`
- Value: the base64 string from the previous step

### 5. Push and run

Push to GitHub. The workflow runs automatically every day at 9 AM ET, or trigger it manually from the Actions tab.

## Session expiry

TikTok sessions last ~6 months. When the workflow fails with a session error, repeat steps 3–4 to refresh it.

## Files

| File | Purpose |
|------|---------|
| `send_streak.py` | Main script — checks idempotency, sends DM, updates state |
| `setup_session.py` | One-time setup — converts browser cookies to Playwright session |
| `config.json` | Friend info, timezone, video URLs |
| `streak_state.json` | Tracks last send date (auto-committed by workflow) |
| `.github/workflows/daily_streak.yml` | GitHub Actions cron workflow |
