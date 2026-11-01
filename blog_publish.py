import argparse
import re
import subprocess
import sys
from pathlib import Path

from blog_convert import convert, DEFAULT_QUALITY

LANDING_REPO = Path(r"C:\Code\WebApp-SchuahSolutions-WebDevLandingPage")
# Publishing uses its own checkout so it never commits onto whatever branch is checked
# out in the landing page folder. Detached, so it never holds `main` checked out.
PUBLISH_CHECKOUT = Path(r"C:\Code\Python-MetaPostingTools\sessions\landing-publish")


def parse_frontmatter(md_path: Path) -> dict:
    content = md_path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        print("ERROR: Could not find frontmatter in markdown file.")
        sys.exit(1)
    result = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def add_path_entry(paths_ts: Path, slug: str) -> None:
    content = paths_ts.read_text(encoding="utf-8")
    entry = f'  "/blogs/{slug}",'
    if entry in content:
        print(f"  Path /blogs/{slug} already exists in paths.ts — skipping.")
        return
    # Insert after the last /blogs/ line
    lines = content.splitlines()
    last_blog_idx = None
    for i, line in enumerate(lines):
        if '"/blogs/' in line:
            last_blog_idx = i
    if last_blog_idx is None:
        print("ERROR: Could not find existing /blogs/ entries in paths.ts.")
        sys.exit(1)
    lines.insert(last_blog_idx + 1, entry)
    paths_ts.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Added /blogs/{slug} to paths.ts")


def git(args: list, cwd: Path) -> str:
    result = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR (git {' '.join(args)}):\n{result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def publish_checkout() -> Path:
    """The publish checkout, created if missing and moved to the latest origin/main."""
    if not PUBLISH_CHECKOUT.exists():
        git(["fetch", "origin", "main"], LANDING_REPO)
        git(["worktree", "add", "--detach", str(PUBLISH_CHECKOUT), "origin/main"], LANDING_REPO)
    git(["fetch", "origin", "main"], PUBLISH_CHECKOUT)
    git(["checkout", "--detach", "origin/main"], PUBLISH_CHECKOUT)
    return PUBLISH_CHECKOUT


def main():
    parser = argparse.ArgumentParser(description="Publish a blog post to the live landing page (main).")
    parser.add_argument("blog", help="Path to the blog .md file")
    parser.add_argument("image", help="Path to the cover image PNG")
    parser.add_argument("--quality", type=int, default=DEFAULT_QUALITY, metavar="1-100",
                        help=f"WEBP quality. Default: {DEFAULT_QUALITY}")
    args = parser.parse_args()

    blog_path = Path(args.blog)
    image_path = Path(args.image)
    for path in (blog_path, image_path):
        if not path.exists():
            print(f"ERROR: Not found: {path}")
            sys.exit(1)

    fm = parse_frontmatter(blog_path)
    slug = fm.get("slug")
    if not slug:
        print("ERROR: 'slug' not found in frontmatter.")
        sys.exit(1)
    print(f"\n  Blog: {fm.get('title', slug)}\n  Slug: {slug}\n")

    checkout = publish_checkout()
    landing = checkout / "landing-page"

    dest_md = landing / "src" / "blogs" / f"{slug}.md"
    if dest_md.exists():
        print(f"  WARNING: {dest_md.name} already exists — overwriting.")
    dest_md.write_text(blog_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  Copied markdown → {dest_md}")

    paths_ts = landing / "src" / "app" / "paths.ts"
    add_path_entry(paths_ts, slug)

    print("  Converting image...")
    webp_dir = landing / "public" / "blogs"
    convert(image_path, slug, args.quality, force=True, target_dir=webp_dir)

    git(["add", str(dest_md), str(paths_ts), str(webp_dir / f"{slug}.webp")], checkout)
    git(["commit", "-m", f"feat: Add blog post '{slug}'"], checkout)
    git(["push", "origin", "HEAD:main"], checkout)
    print("\n  Published: pushed to main, which is live.\n")


if __name__ == "__main__":
    main()
