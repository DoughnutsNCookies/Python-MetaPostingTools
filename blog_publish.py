import argparse
import re
import subprocess
import sys
from pathlib import Path

from convert import convert, DEFAULT_QUALITY

GH_CLI = r"C:\Program Files\GitHub CLI\gh.exe"
LANDING_PAGE = Path(r"C:\Code\WebApp-SchuahSolutions-WebDevLandingPage")


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


def main():
    parser = argparse.ArgumentParser(
        description="Publish a new blog post to the landing page and create a PR."
    )
    parser.add_argument("blog", help="Path to the blog .md file")
    parser.add_argument("image", help="Path to the cover image PNG")
    parser.add_argument(
        "--worktree",
        default=str(LANDING_PAGE),
        help=f"Path to the worktree (or landing page root). Default: {LANDING_PAGE}",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        metavar="1-100",
        help=f"WEBP quality. Default: {DEFAULT_QUALITY}",
    )
    args = parser.parse_args()

    blog_path = Path(args.blog)
    image_path = Path(args.image)
    worktree = Path(args.worktree)
    landing = worktree / "landing-page"

    if not blog_path.exists():
        print(f"ERROR: Blog file not found: {blog_path}")
        sys.exit(1)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)
    if not landing.exists():
        print(f"ERROR: landing-page directory not found at: {landing}")
        sys.exit(1)

    # 1. Parse slug from frontmatter
    fm = parse_frontmatter(blog_path)
    slug = fm.get("slug")
    title = fm.get("title", slug)
    if not slug:
        print("ERROR: 'slug' not found in frontmatter.")
        sys.exit(1)
    print(f"\n  Blog: {title}")
    print(f"  Slug: {slug}\n")

    # 2. Copy markdown file
    dest_md = landing / "src" / "blogs" / f"{slug}.md"
    if dest_md.exists():
        print(f"  WARNING: {dest_md.name} already exists — overwriting.")
    dest_md.write_text(blog_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"  Copied markdown → {dest_md}")

    # 3. Add path entry to paths.ts
    paths_ts = landing / "src" / "app" / "paths.ts"
    add_path_entry(paths_ts, slug)

    # 4. Convert PNG to WEBP
    print(f"  Converting image...")
    webp_dir = landing / "public" / "blogs"
    convert(image_path, slug, args.quality, force=True, target_dir=webp_dir)

    # 5. Commit and push
    branch = git(["rev-parse", "--abbrev-ref", "HEAD"], worktree)
    print(f"  Branch: {branch}")
    git(["add", str(dest_md), str(paths_ts), str(webp_dir / f"{slug}.webp")], worktree)
    git(["commit", "-m", f"feat: Add blog post '{slug}'"], worktree)
    git(["push", "origin", f"HEAD:{branch}"], worktree)
    print(f"  Pushed to {branch}")

    # 6. Create PR
    print("\n  Creating PR...")
    result = subprocess.run(
        [GH_CLI, "pr", "create", "--base", "main",
         "--title", f"feat: Add blog post — {title}",
         "--body", f"Adds blog post `{slug}`.\n\n- `src/blogs/{slug}.md`\n- `public/blogs/{slug}.webp`\n- Path entry in `paths.ts`"],
        cwd=worktree,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR creating PR:\n{result.stderr.strip()}")
        sys.exit(1)
    pr_url = result.stdout.strip()
    print(f"\n  PR created: {pr_url}\n")


if __name__ == "__main__":
    main()
