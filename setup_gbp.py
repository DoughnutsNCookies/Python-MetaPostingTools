import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session_gbp.json")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        print("\n  Opening Google Business Profile...")
        page.goto("https://business.google.com")

        input("  Log in fully, then press Enter to save session...")

        context.storage_state(path=SESSION_FILE)
        print(f"  Session saved to {SESSION_FILE}\n")
        browser.close()


if __name__ == "__main__":
    main()
