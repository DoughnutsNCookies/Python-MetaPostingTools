"""Meta posts that were too far ahead to schedule yet (Meta only allows 29 days).

  python meta_pending.py add <slug> <YYYY-MM-DD> <image.png> <caption.txt>
  python meta_pending.py due      # JSON list of pending posts that can be scheduled now
  python meta_pending.py done <slug>

`add` copies the image and caption into sessions\\meta_pending\\, so they survive the
batch folder being cleaned up.
"""

import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from scheduling import MYT, POST_HOUR

PENDING_DIR = Path(r"C:\Code\Python-MetaPostingTools\sessions\meta_pending")
PENDING_FILE = PENDING_DIR / "pending.json"
META_LIMIT = timedelta(days=29)
# A run takes a while; leave room so a post that's "due" is still inside the window when posted.
SAFETY = timedelta(hours=3)


def load():
    return json.loads(PENDING_FILE.read_text(encoding="utf-8")) if PENDING_FILE.exists() else []


def save(items):
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def add(slug, day, image, caption):
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    img = PENDING_DIR / f"{slug}-social.png"
    cap = PENDING_DIR / f"{slug}.caption.txt"
    shutil.copyfile(image, img)
    shutil.copyfile(caption, cap)
    items = [i for i in load() if i["slug"] != slug]
    items.append({"slug": slug, "date": day, "image": str(img), "caption": str(cap)})
    save(items)
    print(f"Added {slug} ({day}) to the Meta waiting list.")


def due():
    now = datetime.now(MYT)
    out = []
    for item in load():
        when = datetime.fromisoformat(item["date"]).replace(hour=POST_HOUR, tzinfo=MYT)
        if now + timedelta(hours=1) <= when <= now + META_LIMIT - SAFETY:
            out.append(item)
        elif when < now + timedelta(hours=1):
            out.append({**item, "missed": True})
    print(json.dumps(out, indent=2))


def done(slug):
    item = next((i for i in load() if i["slug"] == slug), None)
    save([i for i in load() if i["slug"] != slug])
    if item:
        Path(item["image"]).unlink(missing_ok=True)
        Path(item["caption"]).unlink(missing_ok=True)
    print(f"Removed {slug} from the Meta waiting list.")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "add" and len(args) == 4:
        add(*args)
    elif cmd == "due" and not args:
        due()
    elif cmd == "done" and len(args) == 1:
        done(*args)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
