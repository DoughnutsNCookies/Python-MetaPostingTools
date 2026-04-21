import argparse
import sys
from pathlib import Path
from PIL import Image

TARGET_DIR = Path(
    r"C:\Code\WebApp-SchuahSolutions-WebDevLandingPage\landing-page\public\blogs"
)

DEFAULT_QUALITY = 82


def format_size(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    else:
        return f"{bytes_count / (1024 * 1024):.2f} MB"


def convert(input_path: Path, slug: str, quality: int, force: bool, target_dir: Path) -> None:
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".png":
        print(f"ERROR: Input file must be a PNG. Got: {input_path.suffix}")
        sys.exit(1)

    if not all(c.isalnum() or c == "-" for c in slug):
        print(f"ERROR: Slug must contain only letters, numbers, and hyphens. Got: {slug!r}")
        sys.exit(1)

    if slug != slug.lower():
        print(f"ERROR: Slug must be lowercase. Got: {slug!r}")
        sys.exit(1)

    output_path = target_dir / f"{slug}.webp"

    if output_path.exists() and not force:
        print(f"ERROR: Output file already exists: {output_path}")
        print(f"  Use --force to overwrite it.")
        sys.exit(1)

    if not target_dir.exists():
        print(f"ERROR: Target directory does not exist: {target_dir}")
        print(f"  Is the landing page project at the expected location?")
        sys.exit(1)

    input_size = input_path.stat().st_size

    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        img.save(output_path, format="WEBP", quality=quality, method=6)

    output_size = output_path.stat().st_size
    savings_pct = (1 - output_size / input_size) * 100

    print(f"\n  Input:   {input_path.name}")
    print(f"  Output:  {output_path}")
    print(f"  Quality: {quality}")
    print(f"\n  Before:  {format_size(input_size)}")
    print(f"  After:   {format_size(output_size)}")
    print(f"  Savings: {savings_pct:.1f}%")
    print(f"\n  Done.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a PNG to WEBP and save it to the blog images directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python blog_convert.py hero.png my-new-blog-post
  python blog_convert.py C:/Users/schuah/Downloads/hero.png my-blog-post --quality 85
  python blog_convert.py hero.png existing-slug --force
        """,
    )
    parser.add_argument("input", help="Path to the source PNG file")
    parser.add_argument("slug", help="Output slug (e.g. 'my-blog-post'). Lowercase, hyphens only, no extension.")
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        choices=range(1, 101),
        metavar="1-100",
        help=f"WEBP quality (1-100). Default: {DEFAULT_QUALITY}",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite if output already exists.")

    parser.add_argument(
        "--target",
        default=str(TARGET_DIR),
        help=f"Override output directory. Default: {TARGET_DIR}",
    )

    args = parser.parse_args()
    convert(Path(args.input), args.slug, args.quality, args.force, Path(args.target))


if __name__ == "__main__":
    main()
