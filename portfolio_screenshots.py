"""Capture the top of a client website: a square for social media, a landscape for the website.

  python portfolio_screenshots.py https://example.com --square sq.png --landscape ls.png

Square is 1026x1026, landscape 2052x1026: plain viewport captures, no device frame.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

SIZES = {"square": (1026, 1026), "landscape": (2052, 1026)}
# Give hero sliders, fonts and fade-in animations time to settle.
SETTLE_MS = 4000


def capture(url: str, outputs: dict):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for kind, out in outputs.items():
            w, h = SIZES[kind]
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(SETTLE_MS)
            page.screenshot(path=str(out))
            page.close()
            print(f"  {kind}: {out} ({w}x{h})")
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--square", type=Path, required=True)
    ap.add_argument("--landscape", type=Path, required=True)
    a = ap.parse_args()
    capture(a.url, {"square": a.square, "landscape": a.landscape})


if __name__ == "__main__":
    main()
