import argparse
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

BLOG_BASE_URL = "https://schuahsolutions.com/blogs"
CDP_URL = "http://localhost:9222"


def adapt_caption(caption: str) -> str:
    lines = caption.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().lower().startswith("read it now"):
            lines[i] = 'Read it now by clicking on the "Learn more" button'
            break
    return "\n".join(lines)


def gbp_post(image_path: Path, slug: str, caption: str):
    blog_url = f"{BLOG_BASE_URL}/{slug}"
    adapted_caption = adapt_caption(caption)

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception:
            print("\n  ERROR: Could not connect to Chrome.")
            print("  Run start_chrome_gbp.bat first, then re-run this script.\n")
            sys.exit(1)

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        print("\n  Opening Google Business Profile...")
        page.goto("https://business.google.com")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Save debug screenshot
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
            "button:has-text('Post')",
        ]:
            try:
                page.locator(selector).first.click(timeout=5000)
                added = True
                break
            except Exception:
                continue

        if not added:
            print(f"  ERROR: Could not find post button. Screenshot saved to {screenshot_path}")
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
