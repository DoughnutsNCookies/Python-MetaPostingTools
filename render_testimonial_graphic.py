"""Render a testimonial's square social post (1080x1080) from a WhatsApp chat screenshot.

  python render_testimonial_graphic.py chat.png --prefix "Walk-ins still lead, but " \
      --highlight "Google Ads orders are coming in" --suffix "." --accent "#3d85c6" --out post.png

Logo top-right, a headline in three runs (dark / accent / dark, suffix may be empty), and
the chat screenshot below it, scaled to fill the space (at most 1.8x so it stays sharp).
"""

import argparse
import base64
import html
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).with_name("assets")
DARK = "#424242"
SIZE = 1080
MAX_UPSCALE = 1.8

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Anton; src: url("data:font/ttf;base64,{font}"); }}
html, body {{ margin: 0; background: #fff; }}
.page {{ position: relative; width: {size}px; height: {size}px; overflow: hidden; background: #fff;
         box-sizing: border-box; padding: 110px 70px 70px; display: flex; flex-direction: column; gap: 44px; }}
.logo {{ position: absolute; top: 20px; right: 20px; width: 144px; }}
.title {{ font-family: Anton, sans-serif; font-size: 70px; line-height: 0.95; color: {dark};
          text-align: center; }}
.title b {{ font-weight: normal; color: {accent}; }}
.chat {{ flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }}
.chat img {{ display: block; border-radius: 18px; border: 1px solid #dddddd; }}
</style></head><body><div class="page">
<img class="logo" src="data:image/webp;base64,{logo}">
<div class="title">{prefix}<b>{highlight}</b>{suffix}</div>
<div class="chat"><img src="data:image/png;base64,{chat}"></div>
</div></body></html>"""


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def render(chat: Path, prefix: str, highlight: str, suffix: str, accent: str, out: Path):
    chat_png = Path(out).with_suffix(".chat.png")
    Image.open(chat).convert("RGB").save(chat_png)  # normalise webp/jpg screenshots to PNG
    chat_w, chat_h = Image.open(chat_png).size
    page_html = PAGE.format(font=b64(ASSETS / "Anton-Regular.ttf"), logo=b64(ASSETS / "logo.webp"),
                            chat=b64(chat_png), size=SIZE, dark=DARK, accent=accent,
                            prefix=html.escape(prefix), highlight=html.escape(highlight),
                            suffix=html.escape(suffix))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": SIZE, "height": SIZE})
        page.set_content(page_html)
        page.evaluate("document.fonts.ready")
        # A headline over three lines squeezes the chat too small to read.
        lines = page.evaluate("""() => {
            const t = document.querySelector('.title');
            return Math.round(t.getBoundingClientRect().height / (70 * 0.95));
        }""")
        if lines > 3:
            raise SystemExit(f"ERROR: headline runs to {lines} lines; keep it to 3. Shorten it.")
        # Fit the screenshot to the space left, keeping its shape so the border hugs it.
        page.evaluate(f"""() => {{
            const box = document.querySelector('.chat').getBoundingClientRect();
            const s = Math.min(box.width / {chat_w}, box.height / {chat_h}, {MAX_UPSCALE});
            const img = document.querySelector('.chat img');
            img.style.width = ({chat_w} * s) + 'px';
            img.style.height = ({chat_h} * s) + 'px';
        }}""")
        page.screenshot(path=str(out))
        browser.close()
    chat_png.unlink()
    print(f"  testimonial: {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chat", type=Path, help="WhatsApp chat screenshot")
    ap.add_argument("--prefix", required=True, help="Dark text before the highlight")
    ap.add_argument("--highlight", required=True, help="Accent-coloured words")
    ap.add_argument("--suffix", default="", help="Dark text after the highlight (may be empty)")
    ap.add_argument("--accent", default="#e29d5f", help="Highlight colour (hex)")
    ap.add_argument("--out", type=Path, required=True, help="Output PNG, 1080x1080")
    a = ap.parse_args()
    render(a.chat, a.prefix, a.highlight, a.suffix, a.accent, a.out)


if __name__ == "__main__":
    main()
