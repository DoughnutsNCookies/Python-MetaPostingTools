"""
One-time setup: logs into LinkedIn manually and saves the session.
Run this once, then use linkedin_post.py for all future posts.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

SESSIONS_DIR = Path(r"C:\Code\Python-MetaPostingTools\sessions")
SESSION_FILE = SESSIONS_DIR / "session_linkedin.json"


def main():
    print("\n  Opening LinkedIn in a browser window.")
    print("  Log in as the managing account, then come back here and press Enter.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        page.goto("https://www.linkedin.com/login")
        input("  Press Enter once you are fully logged in and can see your feed... ")

        SESSIONS_DIR.mkdir(exist_ok=True)
        context.storage_state(path=SESSION_FILE)
        print(f"\n  Session saved to {SESSION_FILE}")
        print("  You won't need to log in again until the session expires.\n")

        browser.close()


if __name__ == "__main__":
    main()
