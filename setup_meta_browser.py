"""
One-time setup: logs into Meta Business Suite manually and saves the session.
Run this once, then use meta_post.py for all future posts.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SESSIONS_DIR = Path(r"C:\Code\Python-MetaPostingTools\sessions")
SESSION_FILE = SESSIONS_DIR / "session.json"


def main():
    print("\n  Opening Meta Business Suite in a browser window.")
    print("  Log in manually (including 2FA), then come back here and press Enter.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        page.goto("https://business.facebook.com")
        input("  Press Enter once you are fully logged in and can see the dashboard... ")

        SESSIONS_DIR.mkdir(exist_ok=True)
        context.storage_state(path=SESSION_FILE)
        print(f"\n  Session saved to {SESSION_FILE}")
        print("  You won't need to log in again until the session expires.\n")

        browser.close()


if __name__ == "__main__":
    main()
