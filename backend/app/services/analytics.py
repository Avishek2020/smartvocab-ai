"""Dashboard metrics computed from the user's own rows. No placeholder numbers."""
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Date, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models import LearningStatistic, ReviewHistory, User, VocabularyCard
from app.schemas.analytics import DashboardOut, DayActivity

DIFFICULT_LAPSES = 3
DIFFICULT_EASE = 1.8


def _streak(active_days: set[date], today: date) -> int:
    # A streak survives until the end of today: if nothing yet today, count from yesterday.
    day = today if today in active_days else today - timedelta(days=1)
    n = 0
    while day in active_days:
        n += 1
        day -= timedelta(days=1)
    return n


def dashboard(db: Session, user: User, now: datetime | None = None) -> DashboardOut:
    prefs = user.preferences
    tz = ZoneInfo(prefs.timezone)
    now = now or datetime.now(UTC)
    today = now.astimezone(tz).date()
    start_today = datetime.combine(today, datetime.min.time(), tz)
    uid = user.id
    C, R = VocabularyCard, ReviewHistory

    total = db.scalar(select(func.count()).where(C.user_id == uid, C.status != "draft")) or 0
    new_today = db.scalar(select(func.count()).where(C.user_id == uid, C.status != "draft",
                                                     C.created_at >= start_today)) or 0
    mastered = db.scalar(select(func.count()).where(C.user_id == uid, C.status == "mastered")) or 0
    due_now = db.scalar(select(func.count()).where(
        C.user_id == uid, C.status.in_(("new", "learning", "review")),
        or_(C.due_at.is_(None), C.due_at <= now))) or 0
    difficult = db.scalar(select(func.count()).where(
        C.user_id == uid, C.status != "draft",
        or_(C.lapses >= DIFFICULT_LAPSES, C.ease_factor < DIFFICULT_EASE))) or 0

    cefr_col = func.coalesce(C.cefr_level, "unknown")
    cefr = dict(db.execute(select(cefr_col, func.count())
                           .where(C.user_id == uid, C.status != "draft").group_by(cefr_col)).all())
    status = dict(db.execute(select(C.status, func.count()).where(C.user_id == uid).group_by(C.status)).all())

    local_day = lambda col: cast(func.timezone(prefs.timezone, col), Date)  # noqa: E731
    week_start = today - timedelta(days=6)
    c_day, r_day = local_day(C.created_at), local_day(R.reviewed_at)
    added = dict(db.execute(
        select(c_day, func.count())
        .where(C.user_id == uid, C.status != "draft", C.created_at >= start_today - timedelta(days=6))
        .group_by(c_day)).all())
    reviews = dict(db.execute(
        select(r_day, func.count())
        .where(R.user_id == uid, R.reviewed_at >= start_today - timedelta(days=6)).group_by(r_day)).all())
    last_7 = [DayActivity(day=week_start + timedelta(days=i),
                          cards_added=added.get(week_start + timedelta(days=i), 0),
                          reviews=reviews.get(week_start + timedelta(days=i), 0)) for i in range(7)]

    # Streak: any day with a review or a new card, looking back up to a year.
    since = start_today - timedelta(days=366)
    review_days = set(db.scalars(select(local_day(R.reviewed_at)).where(R.user_id == uid, R.reviewed_at >= since).distinct()))
    card_days = set(db.scalars(select(local_day(C.created_at)).where(C.user_id == uid, C.status != "draft", C.created_at >= since).distinct()))
    streak = _streak(review_days | card_days, today)

    total_30, good_30 = db.execute(
        select(func.count(), func.count().filter(R.rating != "again"))
        .where(R.user_id == uid, R.reviewed_at >= now - timedelta(days=30))).one()
    retention = round(good_30 / total_30, 3) if total_30 else None

    seconds_7d = db.scalar(select(func.coalesce(func.sum(LearningStatistic.seconds_studied), 0))
                           .where(LearningStatistic.user_id == uid, LearningStatistic.day >= week_start)) or 0

    recs: list[str] = []
    if total == 0:
        recs.append("Add your first words to start building your vocabulary.")
    else:
        if due_now:
            recs.append(f"You have {due_now} card{'s' if due_now != 1 else ''} ready to review.")
        if new_today < prefs.daily_new_cards:
            left = prefs.daily_new_cards - new_today
            recs.append(f"Add {left} more word{'s' if left != 1 else ''} today to reach your daily goal.")
        if difficult:
            recs.append(f"{difficult} difficult word{'s' if difficult != 1 else ''} could use extra practice.")
    reviews_today = reviews.get(today, 0)

    return DashboardOut(
        total_cards=total, new_today=new_today, mastered=mastered, due_now=due_now, difficult=difficult,
        streak_days=streak, reviews_today=reviews_today, retention_30d=retention,
        minutes_studied_7d=int(seconds_7d // 60), cefr_distribution=cefr, status_distribution=status,
        last_7_days=last_7, daily_new_goal=prefs.daily_new_cards, recommendations=recs,
    )
