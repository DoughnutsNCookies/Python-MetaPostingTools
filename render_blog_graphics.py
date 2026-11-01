"""Render a blog's square social post (1080x1080) and landscape website cover (1920x1080).

Same layout as the old Canva templates: logo top-right, illustration, and a title in
three runs (dark / accent / dark). The illustration is an SVG file Claude draws per blog.
"""

import argparse
import base64
import html
from pathlib import Path

from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).with_name("assets")
DARK = "#424242"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Anton; src: url("data:font/ttf;base64,{font}"); }}
html, body {{ margin: 0; background: #fff; }}
.page {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; background: #fff; }}
.logo {{ position: absolute; top: 20px; right: 20px; width: {logo_w}px; }}
.art {{ position: absolute; left: {art_x}px; top: {art_y}px; width: {art_w}px; height: {art_h}px;
        object-fit: contain; }}
.title {{ position: absolute; left: {title_x}px; width: {title_w}px; {title_pos}
          font-family: Anton, sans-serif; font-size: {size}px; line-height: 0.9;
          color: {dark}; text-align: {align}; }}
.title b {{ font-weight: normal; color: {accent}; }}
</style></head><body><div class="page">
<img class="logo" src="data:image/webp;base64,{logo}">
<img class="art" src="data:image/svg+xml;base64,{art}">
<div class="title">{prefix}<b>{highlight}</b>{suffix}</div>
</div></body></html>"""

LAYOUTS = {
    "social": dict(w=1080, h=1080, logo_w=144, art_x=252, art_y=200, art_w=576, art_h=432,
                   title_x=108, title_w=864, title_pos="top: 680px;", size=80, align="center"),
    "cover": dict(w=1920, h=1080, logo_w=200, art_x=108, art_y=259, art_w=750, art_h=562,
                  title_x=960, title_w=852, title_pos="top: 50%; transform: translateY(-50%);",
                  size=139, align="left"),
}


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def render(svg: Path, prefix: str, highlight: str, suffix: str, accent: str, outputs: dict):
    common = dict(font=b64(ASSETS / "Anton-Regular.ttf"), logo=b64(ASSETS / "logo.webp"),
                  art=b64(svg), dark=DARK, accent=accent, prefix=html.escape(prefix),
                  highlight=html.escape(highlight), suffix=html.escape(suffix))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for kind, out in outputs.items():
            layout = LAYOUTS[kind]
            page = browser.new_page(viewport={"width": layout["w"], "height": layout["h"]})
            page.set_content(PAGE.format(**common, **layout))
            page.evaluate("document.fonts.ready")
            # A title that runs past the bottom (square) or edge (cover) means it's too long.
            overflow = page.evaluate("""() => {
                const t = document.querySelector('.title').getBoundingClientRect();
                return t.bottom > innerHeight - 40 || t.top < 90;
            }""")
            if overflow:
                raise SystemExit(f"ERROR: title doesn't fit the {kind} layout. Shorten it.")
            page.screenshot(path=str(out))
            page.close()
            print(f"  {kind}: {out}")
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("svg", type=Path, help="Illustration SVG")
    ap.add_argument("--prefix", required=True, help="Dark text before the highlight")
    ap.add_argument("--highlight", required=True, help="Accent-coloured keyword")
    ap.add_argument("--suffix", required=True, help="Dark text after the highlight")
    ap.add_argument("--accent", default="#e29d5f", help="Highlight colour (hex)")
    ap.add_argument("--social", type=Path, required=True, help="Output PNG, 1080x1080")
    ap.add_argument("--cover", type=Path, required=True, help="Output PNG, 1920x1080")
    a = ap.parse_args()
    render(a.svg, a.prefix, a.highlight, a.suffix, a.accent, {"social": a.social, "cover": a.cover})


if __name__ == "__main__":
    main()
