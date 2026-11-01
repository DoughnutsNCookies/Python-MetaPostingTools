"""Work out which Tuesdays the monthly blog run must fill, and list the existing posts.

Each published blog's frontmatter date is its posting Tuesday, so the latest date on the
site is the last Tuesday already covered. The run fills every Tuesday after that through
the end of the current month. (Meta only schedules 29 days ahead, so a Tuesday on the
30th/31st can't go to Meta on the 1st; those go on the meta_pending.py waiting list.)
"""

import json
import re
import sys
from datetime import datetime, timedelta

from blog_publish import publish_checkout
from scheduling import MYT, POST_HOUR

MIN_LEAD = timedelta(hours=1)
TUESDAY = 1


def read_blogs():
    blogs_dir = publish_checkout() / "landing-page" / "src" / "blogs"
    blogs = []
    for md in sorted(blogs_dir.glob("*.md")):
        fm = dict(re.findall(r'^(\w+):\s*"(.*)"\s*$', md.read_text(encoding="utf-8"), re.M))
        try:
            day = datetime.strptime(fm.get("date", "").title(), "%d %B %Y").date()
        except ValueError:
            day = None
        blogs.append({"slug": md.stem, "title": fm.get("title", md.stem),
                      "date": day.isoformat() if day else None})
    return blogs


def tuesdays_to_fill(blogs, now):
    dated = [b["date"] for b in blogs if b["date"]]
    last = datetime.fromisoformat(max(dated)).replace(tzinfo=MYT) if dated else now
    start = max(last + timedelta(days=1), now + MIN_LEAD)
    day = start.replace(hour=POST_HOUR, minute=0, second=0, microsecond=0)
    if day < start:
        day += timedelta(days=1)
    day += timedelta(days=(TUESDAY - day.weekday()) % 7)
    out = []
    while day.month == now.month and day.year == now.year:
        out.append(day.date().isoformat())
        day += timedelta(days=7)
    return last.date().isoformat(), out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    now = datetime.now(MYT)
    blogs = read_blogs()
    last, tuesdays = tuesdays_to_fill(blogs, now)
    print(json.dumps({
        "now": now.isoformat(timespec="minutes"),
        "last_scheduled": last,
        "tuesdays_to_fill": tuesdays,
        "existing_posts": sorted(blogs, key=lambda b: b["date"] or "", reverse=True),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
