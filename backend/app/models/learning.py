import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPk

RATINGS = ("again", "hard", "good", "easy")


class ReviewSession(UUIDPk, Timestamps, Base):
    __tablename__ = "review_sessions"
    __table_args__ = (Index("ix_review_sessions_user_started", "user_id", "started_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="flashcard", nullable=False)  # flashcard | reverse | quiz | listening ...
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary_collections.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cards_reviewed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ReviewHistory(UUIDPk, Base):
    """Append-only log of every rating. Source of truth for re-computing schedules with a new model."""

    __tablename__ = "review_history"
    __table_args__ = (
        CheckConstraint(f"rating IN {RATINGS}", name="rating"),
        Index("ix_review_history_user_reviewed", "user_id", "reviewed_at"),
        Index("ix_review_history_card_reviewed", "card_id", "reviewed_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vocabulary_cards.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("review_sessions.id", ondelete="SET NULL"))
    rating: Mapped[str] = mapped_column(String(5), nullable=False)
    response_ms: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[int | None] = mapped_column(Integer)
    ease_before: Mapped[float] = mapped_column(Float, nullable=False)
    ease_after: Mapped[float] = mapped_column(Float, nullable=False)
    interval_before: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_after: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduler: Mapped[str] = mapped_column(String(20), default="sm2", nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LearningStatistic(UUIDPk, Timestamps, Base):
    """Daily roll-up per user (written by a nightly job / on review submit)."""

    __tablename__ = "learning_statistics"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_learning_statistics_user_day"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    new_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seconds_studied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quiz_score_avg: Mapped[float | None] = mapped_column(Float)
    pronunciation_score_avg: Mapped[float | None] = mapped_column(Float)


class TutorConversation(UUIDPk, Timestamps, Base):
    __tablename__ = "tutor_conversations"
    __table_args__ = (Index("ix_tutor_conversations_user_updated", "user_id", "updated_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="free", nullable=False)  # free | targeted
    scenario: Mapped[str | None] = mapped_column(String(60))                        # job_interview, doctor, ...
    cefr_level: Mapped[str | None] = mapped_column(String(2))
    target_card_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))


class TutorMessage(UUIDPk, Timestamps, Base):
    __tablename__ = "tutor_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user','assistant','system')", name="role"),
        Index("ix_tutor_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutor_conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    corrections: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    used_card_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    audio_key: Mapped[str | None] = mapped_column(String(300))


class PronunciationAttempt(UUIDPk, Timestamps, Base):
    __tablename__ = "pronunciation_attempts"
    __table_args__ = (Index("ix_pronunciation_attempts_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vocabulary_cards.id", ondelete="CASCADE"))
    recording_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audio_recordings.id", ondelete="SET NULL"))
    expected_text: Mapped[str] = mapped_column(Text, nullable=False)
    recognized_text: Mapped[str | None] = mapped_column(Text)
    accuracy_score: Mapped[float | None] = mapped_column(Float)
    fluency_score: Mapped[float | None] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class DailyLearningGoal(UUIDPk, Timestamps, Base):
    __tablename__ = "daily_learning_goals"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_daily_learning_goals_user_day"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)
    target_new_cards: Mapped[int] = mapped_column(Integer, nullable=False)
    target_reviews: Mapped[int] = mapped_column(Integer, nullable=False)
    focus: Mapped[str | None] = mapped_column(String(60))  # business, exam, conversation ...


class UserMistake(UUIDPk, Timestamps, Base):
    __tablename__ = "user_mistakes"
    __table_args__ = (Index("ix_user_mistakes_user_category", "user_id", "category"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # tutor | review | pronunciation | writing
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tutor_messages.id", ondelete="SET NULL"))
    card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vocabulary_cards.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(40), nullable=False)  # article, case, word_order, conjugation ...
    original: Mapped[str] = mapped_column(Text, nullable=False)
    correction: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    occurrences: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
