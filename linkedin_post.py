import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

SESSION_FILE = os.path.join(os.path.dirname(__file__), "session_linkedin.json")
# Company admin page with share=true opens the post composer directly as the company
COMPANY_POST_URL = "https://www.linkedin.com/company/99303319/admin/page-posts/published/?share=true"
COMPANY_NAME = "Schuah Solutions"
DEBUG_SCREENSHOT = os.path.join(os.path.dirname(__file__), "debug_linkedin.png")


def cdp_click(page, x, y):
    """Click at screen coordinates via CDP, bypassing Playwright's shadow DOM hit-test check."""
    cdp = page.context.new_cdp_session(page)
    cdp.send("Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": x, "y": y,
        "button": "left", "clickCount": 1,
    })
    cdp.send("Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": x, "y": y,
        "button": "left", "clickCount": 1,
    })
    cdp.detach()


def get_shadow_buttons(page):
    """Return all visible interactive elements from all shadow DOM roots on the page."""
    return page.evaluate("""
        () => {
            const results = [];
            const seen = new WeakSet();

            function collectFromRoot(root) {
                root.querySelectorAll(
                    '[role="button"], button, [tabindex="0"], [contenteditable="true"], [role="textbox"]'
                ).forEach(el => {
                    if (seen.has(el)) return;
                    seen.add(el);
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        results.push({
                            aria: el.getAttribute('aria-label') || '',
                            text: (el.textContent || '').trim().slice(0, 40),
                            editable: el.getAttribute('contenteditable') || '',
                            role: el.getAttribute('role') || '',
                            x: rect.x + rect.width / 2,
                            y: rect.y + rect.height / 2,
                        });
                    }
                });
            }

            // BFS over all shadow roots — visit each once, no recursive querySelectorAll
            const queue = [document];
            const visited = new WeakSet();
            while (queue.length > 0) {
                const root = queue.shift();
                if (visited.has(root)) continue;
                visited.add(root);
                collectFromRoot(root);
                root.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot && !visited.has(el.shadowRoot)) {
                        queue.push(el.shadowRoot);
                    }
                });
            }
            return results;
        }
    """)


def find_button(shadow_buttons, *keywords, exclude=None):
    """Find a button matching keywords — exact match preferred over partial."""
    keywords_lower = [k.lower() for k in keywords]
    exclude_lower = [e.lower() for e in (exclude or [])]

    def is_excluded(btn):
        combined = (btn['aria'] + ' ' + btn['text']).lower()
        return any(ex in combined for ex in exclude_lower)

    # Pass 1: exact aria or text match
    for btn in shadow_buttons:
        if is_excluded(btn): continue
        if btn['aria'].lower() in keywords_lower or btn['text'].strip().lower() in keywords_lower:
            return btn
    # Pass 2: text starts with keyword
    for btn in shadow_buttons:
        if is_excluded(btn): continue
        if any(btn['text'].strip().lower().startswith(kw) for kw in keywords_lower):
            return btn
    # Pass 3: contains
    for btn in shadow_buttons:
        if is_excluded(btn): continue
        combined = (btn['aria'] + ' ' + btn['text']).lower()
        if any(kw in combined for kw in keywords_lower):
            return btn
    return None


def get_coming_tuesday_10am() -> datetime:
    """Return the next Tuesday at 10:00 AM (never today even if today is Tuesday)."""
    today = datetime.now()
    days_until_tuesday = (1 - today.weekday()) % 7  # 1 = Tuesday
    if days_until_tuesday == 0:
        days_until_tuesday = 7  # If today is Tuesday, use next week's
    return (today + timedelta(days=days_until_tuesday)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )


def post_to_linkedin(image_path: Path, caption: str, schedule: bool = True):
    if not Path(SESSION_FILE).exists():
        print("ERROR: No LinkedIn session found. Run setup_linkedin_browser.py first.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        # Navigate directly to company admin page — opens composer as Schuah Solutions
        print(f"\n  Opening {COMPANY_NAME} post composer...")
        page.goto(COMPANY_POST_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        # Wait for shadow DOM to populate (retry up to ~15s)
        shadow_btns = []
        for attempt in range(1, 7):
            shadow_btns = get_shadow_buttons(page)
            if find_button(shadow_btns, "add media", "photo", "image", "media"):
                break
            print(f"  Waiting for composer... (attempt {attempt})")
            page.wait_for_timeout(2500)

        # Click "Add media" button via CDP (bypasses shadow DOM interception)
        media_btn = find_button(shadow_btns, "add media", "photo", "image", "media")
        if not media_btn:
            print("ERROR: Composer not open or media button not found.")
            page.screenshot(path=DEBUG_SCREENSHOT)
            browser.close()
            sys.exit(1)

        print("  Uploading image...")
        with page.expect_file_chooser(timeout=8000) as fc_info:
            cdp_click(page, media_btn['x'], media_btn['y'])
        fc_info.value.set_files(str(image_path.resolve()))
        page.wait_for_timeout(3000)

        # Click "Next" in the image Editor modal
        try:
            page.get_by_role("button", name="Next").first.click(timeout=5000)
        except PlaywrightTimeout:
            shadow_btns2 = get_shadow_buttons(page)
            next_btn = find_button(shadow_btns2, "next")
            if next_btn:
                cdp_click(page, next_btn['x'], next_btn['y'])
            else:
                print("  WARNING: Next button not found")
        page.wait_for_timeout(2000)

        # Find the text editor and type caption
        print("  Entering caption...")
        shadow_btns3 = get_shadow_buttons(page)
        text_area = find_button(shadow_btns3, "text editor for creating content",
                                "what do you want to talk", "share your thoughts")
        if not text_area:
            for b in shadow_btns3:
                if b['editable'] == 'true' or b['role'] == 'textbox':
                    text_area = b
                    break

        if text_area:
            cdp_click(page, text_area['x'], text_area['y'])
            page.wait_for_timeout(500)
            page.keyboard.press("Control+a")
            page.keyboard.type(caption)
        else:
            editor = page.locator(".ql-editor, [contenteditable='true']").first
            editor.click()
            editor.fill(caption)

        page.wait_for_timeout(1000)

        shadow_btns4 = get_shadow_buttons(page)

        if schedule:
            # Click the Schedule post (clock) button
            schedule_btn = find_button(shadow_btns4, "schedule post")
            if not schedule_btn:
                print("  WARNING: Schedule button not found — falling back to Post Now")
                schedule = False
            else:
                cdp_click(page, schedule_btn['x'], schedule_btn['y'])
                page.wait_for_timeout(2000)

                target = get_coming_tuesday_10am()
                print(f"  Scheduling for {target.strftime('%A %d %B %Y at %I:%M %p')}...")

                # Find all visible <input> elements via BFS over shadow roots
                def get_all_inputs():
                    return page.evaluate("""
                        () => {
                            const results = [];
                            const visited = new WeakSet();
                            const queue = [document];
                            while (queue.length) {
                                const root = queue.shift();
                                if (visited.has(root)) continue;
                                visited.add(root);
                                root.querySelectorAll('input').forEach(inp => {
                                    const rect = inp.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0) {
                                        results.push({
                                            value: inp.value,
                                            placeholder: inp.placeholder || '',
                                            x: rect.x + rect.width / 2,
                                            y: rect.y + rect.height / 2,
                                        });
                                    }
                                });
                                root.querySelectorAll('*').forEach(el => {
                                    if (el.shadowRoot && !visited.has(el.shadowRoot))
                                        queue.push(el.shadowRoot);
                                });
                            }
                            return results;
                        }
                    """)

                target_day = str(target.day)
                time_str = target.strftime('%I:%M %p').lstrip('0')  # e.g. "10:00 AM"

                all_inputs = get_all_inputs()
                date_inp = next((i for i in all_inputs if '/' in i['value'] and len(i['value']) >= 6), None)
                time_inp = next((i for i in all_inputs
                                 if 'AM' in i['value'].upper() or 'PM' in i['value'].upper()), None)

                # --- Set DATE: click field → calendar opens → click target day cell ---
                if date_inp:
                    print(f"  Setting date to {target.month}/{target.day}/{target.year}...")
                    cdp_click(page, date_inp['x'], date_inp['y'])
                    page.wait_for_timeout(800)

                    day_cell = page.evaluate(f"""
                        () => {{
                            const visited = new WeakSet();
                            const queue = [document];
                            while (queue.length) {{
                                const root = queue.shift();
                                if (visited.has(root)) continue;
                                visited.add(root);
                                for (const el of root.querySelectorAll('button, [role="gridcell"], td')) {{
                                    const text = (el.textContent || '').trim();
                                    const rect = el.getBoundingClientRect();
                                    if (text === '{target_day}' && rect.width > 0 && rect.width <= 50) {{
                                        return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
                                    }}
                                }}
                                root.querySelectorAll('*').forEach(el => {{
                                    if (el.shadowRoot && !visited.has(el.shadowRoot))
                                        queue.push(el.shadowRoot);
                                }});
                            }}
                            return null;
                        }}
                    """)
                    if day_cell:
                        cdp_click(page, day_cell['x'], day_cell['y'])
                        page.wait_for_timeout(500)
                    else:
                        print(f"  WARNING: Day {target_day} not found in calendar")

                # --- Set TIME: click field → dropdown opens → scrollIntoView + click target ---
                # Re-fetch inputs as time field coords may have shifted after date selection
                all_inputs = get_all_inputs()
                time_inp = next((i for i in all_inputs
                                 if 'AM' in i['value'].upper() or 'PM' in i['value'].upper()), None)
                if time_inp:
                    print(f"  Setting time to {time_str}...")
                    cdp_click(page, time_inp['x'], time_inp['y'])
                    page.wait_for_timeout(700)

                    time_coords = page.evaluate(f"""
                        () => {{
                            const target = '{time_str}';
                            const visited = new WeakSet();
                            const queue = [document];
                            while (queue.length) {{
                                const root = queue.shift();
                                if (visited.has(root)) continue;
                                visited.add(root);
                                for (const el of root.querySelectorAll('li, [role="option"], [role="listitem"]')) {{
                                    if ((el.textContent || '').trim() === target) {{
                                        el.scrollIntoView({{block: 'center'}});
                                        const rect = el.getBoundingClientRect();
                                        return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
                                    }}
                                }}
                                root.querySelectorAll('*').forEach(el => {{
                                    if (el.shadowRoot && !visited.has(el.shadowRoot))
                                        queue.push(el.shadowRoot);
                                }});
                            }}
                            return null;
                        }}
                    """)
                    if time_coords:
                        cdp_click(page, time_coords['x'], time_coords['y'])
                        page.wait_for_timeout(500)
                    else:
                        print(f"  WARNING: Time option '{time_str}' not found in dropdown")

                page.wait_for_timeout(500)
                page.screenshot(path=DEBUG_SCREENSHOT)

                # Click "Next" in the schedule modal (not "Save as draft")
                sched_btns = get_shadow_buttons(page)
                next_btn = find_button(sched_btns, "next")
                if next_btn:
                    print(f"  Clicking Next at ({next_btn['x']:.0f},{next_btn['y']:.0f})")
                    cdp_click(page, next_btn['x'], next_btn['y'])
                    page.wait_for_timeout(2000)
                    page.screenshot(path=DEBUG_SCREENSHOT)

                    # Now click "Schedule" to confirm
                    sched_btns2 = get_shadow_buttons(page)
                    confirm_btn = find_button(sched_btns2, "schedule", exclude=["schedule post"])
                    if confirm_btn:
                        print(f"  Clicking Schedule confirm at ({confirm_btn['x']:.0f},{confirm_btn['y']:.0f})")
                        cdp_click(page, confirm_btn['x'], confirm_btn['y'])
                        page.wait_for_timeout(3000)
                    else:
                        print("  WARNING: Schedule confirm button not found")
                        for b in sched_btns2:
                            print(f"    aria='{b['aria']}' text='{b['text'][:30]}' at ({b['x']:.0f},{b['y']:.0f})")
                else:
                    print("  WARNING: Next button not found in schedule modal")
                    for b in sched_btns:
                        print(f"    aria='{b['aria']}' text='{b['text'][:30]}' at ({b['x']:.0f},{b['y']:.0f})")

        if not schedule:
            # Post immediately
            print("  Posting now...")
            post_btn = next(
                (b for b in shadow_btns4 if b['text'].strip() == 'Post' and b['aria'] == ''),
                find_button(shadow_btns4, "post", exclude=["schedule", "anyone"])
            )
            if post_btn:
                cdp_click(page, post_btn['x'], post_btn['y'])
            else:
                page.get_by_role("button", name="Post", exact=True).click()

        page.wait_for_timeout(4000)
        page.screenshot(path=DEBUG_SCREENSHOT)
        target_str = get_coming_tuesday_10am().strftime('%A %d %B at %I:%M %p') if schedule else "now"
        print(f"\n  Done. LinkedIn post scheduled for {target_str} as {COMPANY_NAME}.\n")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Post to LinkedIn company page via browser.")
    parser.add_argument("image", help="Path to the image file (PNG/JPG/WEBP)")
    parser.add_argument("slug", help="Blog slug (unused, kept for consistent CLI interface)")
    parser.add_argument("--caption-file", required=True, help="Path to a .txt file containing the caption")
    parser.add_argument("--post-now", action="store_true",
                        help="Post immediately instead of scheduling for coming Tuesday 10am")
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
    post_to_linkedin(image_path, caption, schedule=not args.post_now)


if __name__ == "__main__":
    main()
