from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MYT = ZoneInfo("Asia/Kuala_Lumpur")
POST_HOUR = 10

WEEKDAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DEFAULT_WEEKDAY = {"blog": "tue", "testimonial": "thu", "portfolio": "wed"}
POST_TYPES = list(DEFAULT_WEEKDAY)


def target_datetime(post_type: str, weekday: str | None = None, week: int = 1) -> datetime:
    """10:00 AM MYT on the coming `weekday` (today counts if it's before 10 AM), plus `week - 1` weeks."""
    now = datetime.now(MYT)
    wd = WEEKDAYS[weekday or DEFAULT_WEEKDAY[post_type]]
    days_ahead = (wd - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= POST_HOUR:
        days_ahead = 7
    days_ahead += 7 * (week - 1)
    return (now + timedelta(days=days_ahead)).replace(hour=POST_HOUR, minute=0, second=0, microsecond=0)


def add_schedule_args(parser):
    parser.add_argument("--type", dest="post_type", choices=POST_TYPES, required=True,
                        help="blog (Tue), testimonial (Thu) or portfolio (Wed)")
    parser.add_argument("--weekday", choices=list(WEEKDAYS),
                        help="Override the post type's default day, e.g. --weekday thu")
    parser.add_argument("--week", type=int, default=1,
                        help="1 = the coming occurrence of the day, 2 = the week after, and so on")
