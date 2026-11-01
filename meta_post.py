import argparse
import os
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

from scheduling import add_schedule_args, target_datetime

load_dotenv()

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# A real Chrome profile (logged in once by hand) keeps Meta's rotating cookies fresh;
# the old storage_state snapshot went stale within about a week.
PROFILE_DIR = Path(r"C:\Code\Python-MetaPostingTools\sessions\chrome_profile_meta")
CDP_PORT = 9223
EXIT_LOGIN_EXPIRED = 3
EXIT_NOT_CONFIRMED = 4
EXIT_DATE_REFUSED = 5
PAGE_ID = os.getenv("META_PAGE_ID", "202884486244813")
BLOG_BASE_URL = "https://schuahsolutions.com/blogs"
# Meta has shipped all of these labels for the upload button at different times.
PHOTO_BUTTON_NAMES = ["Add photo/video", "Add Photo", "Add photo", "Photo/video", "Photo"]


@contextmanager
def meta_chrome():
    """Launch real Chrome on the Meta profile, yield a Playwright browser, then close Chrome cleanly."""
    proc = subprocess.Popen([
        CHROME_EXE, f"--remote-debugging-port={CDP_PORT}", f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run", "--no-default-browser-check", "--window-size=1280,900", "about:blank",
    ])
    endpoint = f"http://127.0.0.1:{CDP_PORT}"
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{endpoint}/json/version", timeout=1)
            break
        except OSError:
            time.sleep(1)
    else:
        proc.kill()
        sys.exit("ERROR: Chrome did not start. Close any Chrome window that is using the Meta profile and retry.")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        try:
            yield browser
        finally:
            # Closing through CDP lets Chrome write its refreshed cookies back to the profile.
            browser.new_browser_cdp_session().send("Browser.close")
    proc.wait(timeout=15)


def schedule_post(image_path: Path, caption: str, slug: str, post_type: str, scheduled_dt: datetime):
    print(f"\n  Scheduling for: {scheduled_dt.strftime('%A, %d %B %Y at %I:%M %p MYT')}\n")

    with meta_chrome() as browser:
        page = browser.contexts[0].new_page()

        print("  Opening Meta Business Suite...")
        page.goto(f"https://business.facebook.com/latest/home?business_id=&asset_id={PAGE_ID}")
        page.wait_for_load_state("networkidle")

        print("  Opening post composer...")
        create = page.get_by_role("button", name="Create post").first
        try:
            create.wait_for(timeout=20000)
        except Exception:
            print("\n  ERROR: Meta login has expired. Run setup_meta_browser.py, log in, close that window, then retry.\n")
            sys.exit(EXIT_LOGIN_EXPIRED)
        create.click()

        print("  Uploading image...")
        # The composer sometimes takes a while to open; keep looking for the upload button.
        upload = None
        for _ in range(30):
            upload = next((b for name in PHOTO_BUTTON_NAMES
                           if (b := page.get_by_role("button", name=name, exact=True)).count()), None)
            if upload:
                break
            page.wait_for_timeout(1000)
        if upload:
            with page.expect_file_chooser() as fc_info:
                upload.first.click(timeout=5000)
            fc_info.value.set_files(str(image_path))
        else:
            labels = [b.get_attribute("aria-label") or (b.text_content() or "")[:40]
                      for b in page.get_by_role("button").all()[:40]]
            print("  Buttons on page:", labels)
            raise RuntimeError("Could not find the photo upload button")
        page.wait_for_timeout(3000)

        print("  Entering caption...")
        if post_type == "blog" and slug:
            blog_link = f"{BLOG_BASE_URL}/{slug}"
            full_caption = caption if blog_link in caption else f"{caption}\n\n{blog_link}"
        else:
            full_caption = caption
        composer = page.get_by_label("Text")
        composer.click()
        composer.fill(full_caption)
        page.wait_for_timeout(1000)

        print("  Setting schedule...")
        page.get_by_text("Set date and time").click()
        page.wait_for_timeout(1500)

        # Date: dd/mm/yyyy format, two fields (Facebook + Instagram)
        date_str = scheduled_dt.strftime("%d/%m/%Y")
        hour_str = str(scheduled_dt.hour)
        minute_str = f"{scheduled_dt.minute:02d}"

        date_inputs = page.locator('input[placeholder="dd/mm/yyyy"]')
        date_inputs.nth(0).click(click_count=3)
        date_inputs.nth(0).fill(date_str)
        date_inputs.nth(1).click(click_count=3)
        date_inputs.nth(1).fill(date_str)

        hour_inputs = page.get_by_label("hours")
        hour_inputs.nth(0).click(click_count=3)
        hour_inputs.nth(0).press_sequentially(hour_str, delay=50)
        hour_inputs.nth(1).click(click_count=3)
        hour_inputs.nth(1).press_sequentially(hour_str, delay=50)

        minute_inputs = page.get_by_label("minutes")
        minute_inputs.nth(0).click(click_count=3)
        minute_inputs.nth(0).press_sequentially(minute_str, delay=50)
        minute_inputs.nth(1).click(click_count=3)
        minute_inputs.nth(1).press_sequentially(minute_str, delay=50)

        page.wait_for_timeout(1000)

        schedule_btn = page.get_by_role("button", name="Schedule", exact=True).first
        if schedule_btn.get_attribute("aria-disabled") == "true":
            page.screenshot(path=str(Path(__file__).with_name("meta_debug.png")))
            print("\n  ERROR: Meta won't let this date be scheduled (Schedule button disabled). See meta_debug.png.\n")
            sys.exit(EXIT_DATE_REFUSED)
        schedule_btn.click()
        try:
            page.get_by_text("Your post is scheduled").first.wait_for(timeout=20000)
        except Exception:
            page.screenshot(path=str(Path(__file__).with_name("meta_debug.png")))
            print("\n  ERROR: Meta did not confirm the schedule. See meta_debug.png and check the Planner before retrying.\n")
            sys.exit(EXIT_NOT_CONFIRMED)
        # The confirmation comes with a "Boost" upsell; dismiss it without boosting.
        later = page.get_by_role("button", name="Maybe later")
        if later.count():
            later.first.click()
            page.wait_for_timeout(1500)
        print("\n  Done. Post scheduled for both Facebook and Instagram.\n")


def main():
    parser = argparse.ArgumentParser(description="Schedule a post to Facebook and Instagram via Meta Business Suite.")
    parser.add_argument("image", help="Path to the image file (PNG/JPG)")
    parser.add_argument("slug", nargs="?", default="", help="Blog slug (e.g. my-blog-post) — required for blog type")
    parser.add_argument("--caption-file", required=True, help="Path to a .txt file containing the caption")
    add_schedule_args(parser)
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    if args.post_type == "blog" and not args.slug:
        print("ERROR: slug is required for blog posts.")
        sys.exit(1)

    caption_path = Path(args.caption_file)
    if not caption_path.exists():
        print(f"ERROR: Caption file not found: {caption_path}")
        sys.exit(1)

    caption = caption_path.read_text(encoding="utf-8").strip()
    scheduled_dt = target_datetime(args.post_type, args.weekday, args.week, args.on_date)
    schedule_post(image_path, caption, args.slug, args.post_type, scheduled_dt)


if __name__ == "__main__":
    main()
