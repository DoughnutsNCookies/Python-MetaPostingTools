import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

BLOG_BASE_URL = "https://schuahsolutions.com/blogs"
CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_USER_DATA = r"C:\Users\schuah\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE = "Profile 2"
DEBUG_PORT = 9222


def adapt_caption(caption: str) -> str:
    lines = caption.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().lower().startswith("read it now"):
            lines[i] = 'Read it now by clicking on the "Learn more" button'
            break
    return "\n".join(lines)


def prepare_temp_profile() -> str:
    print("  Copying Chrome profile to temp directory...")
    temp_dir = tempfile.mkdtemp(prefix="chrome_gbp_")

    # Copy Local State (contains encryption key metadata)
    shutil.copy2(
        os.path.join(CHROME_USER_DATA, "Local State"),
        os.path.join(temp_dir, "Local State"),
    )

    # Copy the profile folder
    src_profile = os.path.join(CHROME_USER_DATA, CHROME_PROFILE)
    dst_profile = os.path.join(temp_dir, CHROME_PROFILE)
    shutil.copytree(src_profile, dst_profile, ignore_dangling_symlinks=True)
    print(f"  Profile copied to {temp_dir}")
    return temp_dir


def gbp_post(image_path: Path, slug: str, caption: str):
    blog_url = f"{BLOG_BASE_URL}/{slug}"
    adapted_caption = adapt_caption(caption)

    # Kill any existing Chrome
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
    time.sleep(2)

    temp_dir = prepare_temp_profile()

    try:
        # Launch Chrome with temp profile + debug port
        subprocess.Popen([
            CHROME_EXE,
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--profile-directory={CHROME_PROFILE}",
            f"--user-data-dir={temp_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ])

        # Wait for debug port to be ready
        print("  Waiting for Chrome to start...")
        for _ in range(20):
            try:
                resp = requests.get(f"http://localhost:{DEBUG_PORT}/json/version", timeout=2)
                if resp.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            print("ERROR: Chrome did not start with debug port in time.")
            sys.exit(1)

        time.sleep(2)

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()

            print("\n  Opening Google Business Profile...")
            page.goto("https://business.google.com")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            # Debug screenshot
            screenshot_path = os.path.join(os.path.dirname(__file__), "gbp_debug.png")
            page.screenshot(path=screenshot_path)

            # Try multiple selectors for the post button
            print("  Opening post composer...")
            added = False
            for selector in [
                "button:has-text('Add update')",
                "a:has-text('Add update')",
                "[aria-label='Add update']",
                "button:has-text('Create post')",
                "button:has-text('Add post')",
            ]:
                try:
                    page.locator(selector).first.click(timeout=5000)
                    added = True
                    break
                except Exception:
                    continue

            if not added:
                print(f"  ERROR: Could not find post button. Check screenshot: {screenshot_path}")
                sys.exit(1)

            page.wait_for_timeout(2000)

            # Upload image
            print("  Uploading image...")
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name="Add photos").click()
            fc_info.value.set_files(str(image_path))
            page.wait_for_timeout(3000)

            # Enter caption
            print("  Entering caption...")
            page.get_by_role("textbox").first.click()
            page.get_by_role("textbox").first.fill(adapted_caption)
            page.wait_for_timeout(1000)

            # Add "Learn more" button
            print("  Adding Learn more button...")
            page.get_by_role("button", name="Add a button").click()
            page.wait_for_timeout(1000)
            page.get_by_role("option", name="Learn more").click()
            page.wait_for_timeout(500)

            # Enter blog URL
            page.get_by_placeholder("Link").fill(blog_url)
            page.wait_for_timeout(500)

            # Publish
            print("  Publishing...")
            page.get_by_role("button", name="Publish").click()
            page.wait_for_timeout(5000)
            print("\n  Done. GBP update posted.\n")

            page.close()

    finally:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], capture_output=True)
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Post an update to Google Business Profile.")
    parser.add_argument("image", help="Path to the image file (PNG)")
    parser.add_argument("slug", help="Blog slug (e.g. my-blog-post)")
    parser.add_argument("--caption-file", required=True, help="Path to caption .txt file")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    caption_path = Path(args.caption_file)
    if not caption_path.exists():
        print(f"ERROR: Caption file not found: {caption_path}")
        sys.exit(1)

    caption = caption_path.read_text(encoding="utf-8").strip()
    gbp_post(image_path, args.slug, caption)


if __name__ == "__main__":
    main()
