"""
One-time setup: connects to a running Chrome (started with --remote-debugging-port=9222),
lets you log into Meta Business Suite the normal way, then saves the session.

Google's OAuth flow refuses to work inside Playwright's own launched Chromium (it detects
automation and hangs on about:blank). CDP attach avoids this by using a real Chrome that
the user drives manually.

USAGE:
  1) Close ALL Chrome windows first.
  2) In PowerShell, start Chrome with debugging enabled (use the & call operator):
       & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\Code\\Python-MetaPostingTools\\sessions\\chrome_profile_meta"
  3) In that Chrome window, log in to https://business.facebook.com (Google OAuth works normally).
  4) Come back here and run this script: python setup_meta_browser.py
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

SESSIONS_DIR = Path(r"C:\Code\Python-MetaPostingTools\sessions")
SESSION_FILE = SESSIONS_DIR / "session_meta.json"
CDP_URL = "http://localhost:9222"


def main():
    print(f"\n  Connecting to Chrome at {CDP_URL} ...")
    print("  (make sure Chrome is running with --remote-debugging-port=9222 and you are logged in)\n")

    SESSIONS_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        if not browser.contexts:
            raise RuntimeError("No browser contexts found. Is Chrome open with a page loaded?")
        context = browser.contexts[0]

        page = context.pages[0] if context.pages else context.new_page()
        if "facebook.com" not in page.url:
            page.goto("https://business.facebook.com")
            page.wait_for_load_state("domcontentloaded")

        context.storage_state(path=SESSION_FILE)
        print(f"\n  Session saved to {SESSION_FILE}")
        print("  You can now close Chrome. meta_post.py will use this session.\n")


if __name__ == "__main__":
    main()
