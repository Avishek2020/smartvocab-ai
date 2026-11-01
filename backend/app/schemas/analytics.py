from datetime import date

from pydantic import BaseModel


class DayActivity(BaseModel):
    day: date
    cards_added: int
    reviews: int


class DashboardOut(BaseModel):
    """Every number here is computed from the user's rows. Metrics that need data the user doesn't
    have yet are null, never placeholder values."""

    total_cards: int
    new_today: int
    mastered: int
    due_now: int
    difficult: int
    streak_days: int
    reviews_today: int
    retention_30d: float | None  # share of non-"again" ratings in the last 30 days
    minutes_studied_7d: int
    cefr_distribution: dict[str, int]
    status_distribution: dict[str, int]
    last_7_days: list[DayActivity]
    daily_new_goal: int
    recommendations: list[str]
