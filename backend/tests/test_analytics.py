from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.db.session import SessionLocal
from app.models import ReviewHistory, User, VocabularyCard
from app.services.analytics import _streak

API = "/api/v1"


def test_empty_dashboard_has_no_fake_numbers(auth_client):
    d = auth_client.get(f"{API}/analytics/dashboard").json()
    assert d["total_cards"] == 0 and d["due_now"] == 0 and d["streak_days"] == 0
    assert d["retention_30d"] is None
    assert len(d["last_7_days"]) == 7
    assert all(day["cards_added"] == 0 and day["reviews"] == 0 for day in d["last_7_days"])
    assert d["recommendations"] == ["Add your first words to start building your vocabulary."]


def test_dashboard_reflects_cards_and_reviews(auth_client):
    for term, cefr in [("Termin", "A2"), ("Besprechung", "B1"), ("Vertrag", "B1")]:
        auth_client.post(f"{API}/vocabulary", json={"term": term, "part_of_speech": "noun", "cefr_level": cefr})
    with SessionLocal() as db:
        user = db.scalar(select(User))
        cards = db.scalars(select(VocabularyCard)).all()
        db.execute(update(VocabularyCard).where(VocabularyCard.id == cards[0].id)
                   .values(status="mastered", due_at=datetime.now(UTC) + timedelta(days=30)))
        db.execute(update(VocabularyCard).where(VocabularyCard.id == cards[1].id).values(lapses=4))
        for rating in ("good", "again", "easy", "good"):
            db.add(ReviewHistory(user_id=user.id, card_id=cards[1].id, rating=rating, ease_before=2.5,
                                 ease_after=2.5, interval_before=1, interval_after=2))
        db.commit()
    d = auth_client.get(f"{API}/analytics/dashboard").json()
    assert d["total_cards"] == 3 and d["new_today"] == 3
    assert d["mastered"] == 1
    assert d["due_now"] == 2          # two cards in "new" status with no due date yet
    assert d["difficult"] == 1
    assert d["reviews_today"] == 4
    assert d["retention_30d"] == 0.75
    assert d["cefr_distribution"] == {"A2": 1, "B1": 2}
    assert d["last_7_days"][-1]["cards_added"] == 3
    assert d["streak_days"] == 1


def test_streak_logic():
    today = datetime(2026, 11, 1).date()
    days = {today - timedelta(days=i) for i in (1, 2, 3)}
    assert _streak(days, today) == 3              # nothing yet today, streak still alive
    assert _streak(days | {today}, today) == 4
    assert _streak({today - timedelta(days=2)}, today) == 0
