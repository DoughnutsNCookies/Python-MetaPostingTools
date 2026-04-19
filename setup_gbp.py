import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session_gbp.json")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("\n  Opening Google Business Profile...")
        print("  Log in fully. Session will be saved automatically once the dashboard loads.\n")
        page.goto("https://business.google.com")

        # Poll until the URL is an authenticated GBP dashboard (not base URL or Google accounts)
        deadline = time.time() + 120
        while time.time() < deadline:
            url = page.url
            if (
                "business.google.com" in url
                and "accounts.google.com" not in url
                and url.rstrip("/") != "https://business.google.com"
            ):
                break
            page.wait_for_timeout(2000)
        else:
            print("ERROR: Timed out waiting for GBP login.")
            sys.exit(1)

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        context.storage_state(path=SESSION_FILE)
        print(f"  Session saved to {SESSION_FILE}\n")
        browser.close()


if __name__ == "__main__":
    main()
