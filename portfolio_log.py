"""Which portfolio is scheduled on which Wednesday (kept in sessions\\portfolio_schedule.json).

  python portfolio_log.py add <YYYY-MM-DD> <domain>
  python portfolio_log.py list
"""

import json
import sys
from pathlib import Path

LOG_FILE = Path(r"C:\Code\Python-MetaPostingTools\sessions\portfolio_schedule.json")


def load():
    return json.loads(LOG_FILE.read_text(encoding="utf-8")) if LOG_FILE.exists() else []


def add(day, domain):
    items = [i for i in load() if i["date"] != day] + [{"date": day, "domain": domain}]
    LOG_FILE.write_text(json.dumps(sorted(items, key=lambda i: i["date"]), indent=2), encoding="utf-8")
    print(f"Logged {domain} for {day}.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "add" and len(args) == 2:
        add(*args)
    elif cmd == "list" and not args:
        print(json.dumps(load(), indent=2))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
