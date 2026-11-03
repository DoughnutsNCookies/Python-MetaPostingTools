"""Which portfolio / testimonial is scheduled on which day (sessions\\<kind>_schedule.json).

  python post_log.py add <portfolio|testimonial> <YYYY-MM-DD> <name>
  python post_log.py list <portfolio|testimonial>
  python post_log.py next testimonial <N>     # the next N free Thursdays for new testimonials
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from scheduling import MYT, POST_HOUR, WEEKDAYS

SESSIONS = Path(r"C:\Code\Python-MetaPostingTools\sessions")
KINDS = {"portfolio": "wed", "testimonial": "thu"}


def log_file(kind):
    return SESSIONS / f"{kind}_schedule.json"


def load(kind):
    f = log_file(kind)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def add(kind, day, name):
    items = [i for i in load(kind) if i["date"] != day] + [{"date": day, "name": name}]
    log_file(kind).write_text(json.dumps(sorted(items, key=lambda i: i["date"]), indent=2), encoding="utf-8")
    print(f"Logged {kind} {name} for {day}.")


def next_free(kind, n, now=None):
    """The next n posting days for `kind` after the last logged one (and at least an hour from now)."""
    now = now or datetime.now(MYT)
    weekday = WEEKDAYS[KINDS[kind]]
    dated = [i["date"] for i in load(kind)]
    after = max([date.fromisoformat(max(dated))] if dated else [], default=now.date() - timedelta(days=1))
    day = after + timedelta(days=1)
    out = []
    while len(out) < n:
        if day.weekday() == weekday and datetime(day.year, day.month, day.day, POST_HOUR, tzinfo=MYT) >= now + timedelta(hours=1):
            out.append(day.isoformat())
        day += timedelta(days=1)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "add" and len(args) == 3 and args[0] in KINDS:
        add(*args)
    elif cmd == "list" and len(args) == 1 and args[0] in KINDS:
        print(json.dumps(load(args[0]), indent=2))
    elif cmd == "next" and len(args) == 2 and args[0] in KINDS:
        print(json.dumps(next_free(args[0], int(args[1]))))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
