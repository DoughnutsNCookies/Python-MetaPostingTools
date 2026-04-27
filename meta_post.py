import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

load_dotenv()

SESSION_FILE = Path(r"C:\Code\Python-MetaPostingTools\sessions\session_meta.json")
PAGE_ID = os.getenv("META_PAGE_ID", "202884486244813")
BLOG_BASE_URL = "https://schuahsolutions.com/blogs"
MYT = ZoneInfo("Asia/Kuala_Lumpur")


def next_tuesday_10am() -> datetime:
    now = datetime.now(MYT)
    days_ahead = (1 - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= 10:
        days_ahead = 7
    return now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)


def next_thursday_10am() -> datetime:
    now = datetime.now(MYT)
    days_ahead = (3 - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= 10:
        days_ahead = 7
    return now.replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)


def schedule_post(image_path: Path, caption: str, slug: str, post_type: str):
    if not Path(SESSION_FILE).exists():
        print("ERROR: No session found. Run setup_meta_browser.py first.")
        sys.exit(1)

    scheduled_dt = next_thursday_10am() if post_type == "testimonial" else next_tuesday_10am()
    print(f"\n  Scheduling for: {scheduled_dt.strftime('%A, %d %B %Y at %I:%M %p MYT')}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        print("  Opening Meta Business Suite...")
        page.goto(f"https://business.facebook.com/latest/home?business_id=&asset_id={PAGE_ID}")
        page.wait_for_load_state("networkidle")

        # Click Create post
        print("  Opening post composer...")
        page.get_by_role("button", name="Create post").click()
        page.wait_for_timeout(2000)

        # Upload image via file chooser
        print("  Uploading image...")
        with page.expect_file_chooser() as fc_info:
            page.get_by_role("button", name="Add photo/video").click()
        file_chooser = fc_info.value
        file_chooser.set_files(str(image_path))
        page.wait_for_timeout(3000)

        # Enter caption
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

        # Enable scheduling
        print("  Setting schedule...")
        page.get_by_text("Set date and time").click()
        page.wait_for_timeout(1500)

        # Set date/time fields
        month = scheduled_dt.strftime("%B")
        day = str(scheduled_dt.day)
        year = str(scheduled_dt.year)
        hour = scheduled_dt.strftime("%I").lstrip("0")
        minute = scheduled_dt.strftime("%M")
        am_pm = scheduled_dt.strftime("%p")

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

        # Schedule
        page.get_by_role("button", name="Schedule").click()
        page.wait_for_timeout(6000)
        print("\n  Done. Post scheduled for both Facebook and Instagram.\n")

        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Schedule a post to Facebook and Instagram via Meta Business Suite.")
    parser.add_argument("image", help="Path to the image file (PNG/JPG)")
    parser.add_argument("slug", nargs="?", default="", help="Blog slug (e.g. my-blog-post) — required for blog type")
    parser.add_argument("--caption-file", required=True, help="Path to a .txt file containing the caption")
    parser.add_argument("--type", dest="post_type", choices=["blog", "testimonial"], required=True,
                        help="Post type: 'blog' (Tuesday) or 'testimonial' (Thursday)")
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
    schedule_post(image_path, caption, args.slug, args.post_type)


if __name__ == "__main__":
    main()
