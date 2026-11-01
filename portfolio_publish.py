"""Add a client website to the portfolio on schuahsolutions.com, if it isn't there yet.

  python portfolio_publish.py https://example.com "Business Name" standard landscape.png

Category is landing, ecommerce or standard. The entry goes to the top of its category in
PortfolioSection.tsx and the landscape screenshot is saved as public/section/portfolio/<domain>.webp.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

from blog_publish import git, publish_checkout

SECTION = Path("landing-page/src/app/sections/PortfolioSection.tsx")
IMAGES = Path("landing-page/public/section/portfolio")
CATEGORIES = ["landing", "ecommerce", "standard"]
WEBP_QUALITY = 82


def domain_of(url: str) -> str:
    host = urlparse(url if "//" in url else f"https://{url}").netloc
    return host.removeprefix("www.")


def insert_entry(source: str, domain: str, name: str, category: str) -> str:
    lines = source.splitlines()
    first = next(i for i, l in enumerate(lines) if f'category: "{category}"' in l)
    # Multi-line entries open with a bare "{" on the line above.
    at = first - 1 if lines[first - 1].strip() == "{" else first
    entry = f'  {{ category: "{category}", url: {json.dumps(domain)}, name: {json.dumps(name, ensure_ascii=False)} }},'
    lines.insert(at, entry)
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("name")
    ap.add_argument("category", choices=CATEGORIES)
    ap.add_argument("landscape", type=Path, help="2052x1026 screenshot (PNG)")
    a = ap.parse_args()

    domain = domain_of(a.url)
    checkout = publish_checkout()
    section = checkout / SECTION
    source = section.read_text(encoding="utf-8")
    if f'url: "{domain}"' in source:
        print(f"  {domain} is already in the website portfolio — nothing to do.")
        return

    section.write_text(insert_entry(source, domain, a.name, a.category), encoding="utf-8")
    webp = checkout / IMAGES / f"{domain}.webp"
    Image.open(a.landscape).convert("RGB").save(webp, "WEBP", quality=WEBP_QUALITY, method=6)
    print(f"  Added {a.name} ({a.category}) and {webp.name} ({webp.stat().st_size // 1024} KB)")

    git(["add", str(section), str(webp)], checkout)
    git(["commit", "-m", f"feat: Add {a.name} to portfolio"], checkout)
    git(["push", "origin", "HEAD:main"], checkout)
    print("  Published: pushed to main, which is live.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
