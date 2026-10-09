import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

from scheduling import add_schedule_args, target_datetime

load_dotenv()

SESSION_FILE = Path(r"C:\Code\Python-MetaPostingTools\sessions\session_meta.json")
PAGE_ID = os.getenv("META_PAGE_ID", "202884486244813")
BLOG_BASE_URL = "https://schuahsolutions.com/blogs"
# Meta has shipped all of these labels for the upload button at different times.
PHOTO_BUTTON_NAMES = ["Add photo/video", "Add Photo", "Add photo", "Photo/video", "Photo"]


def schedule_post(image_path: Path, caption: str, slug: str, post_type: str, scheduled_dt: datetime):
    if not Path(SESSION_FILE).exists():
        print("ERROR: No session found. Run setup_meta_browser.py first.")
        sys.exit(1)

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
        page.wait_for_timeout(5000)

        print("  Uploading image...")
        for name in PHOTO_BUTTON_NAMES:
            btn = page.get_by_role("button", name=name, exact=True)
            if btn.count() == 0:
                continue
            with page.expect_file_chooser() as fc_info:
                btn.first.click(timeout=5000)
            fc_info.value.set_files(str(image_path))
            break
        else:
            labels = [b.get_attribute("aria-label") or (b.text_content() or "")[:40]
                      for b in page.get_by_role("button").all()[:40]]
            print("  Buttons on page:", labels)
            raise RuntimeError("Could not find the photo upload button")
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
    scheduled_dt = target_datetime(args.post_type, args.weekday, args.week)
    schedule_post(image_path, caption, args.slug, args.post_type, scheduled_dt)


if __name__ == "__main__":
    main()
