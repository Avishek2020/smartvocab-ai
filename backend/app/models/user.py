import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPk

CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


class User(UUIDPk, Timestamps, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(CITEXT, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Bumped on logout / password change: invalidates every token issued before.
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    preferences: Mapped["UserPreferences"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class UserPreferences(UUIDPk, Timestamps, Base):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint(f"cefr_level IN {CEFR_LEVELS}", name="cefr_level"),
        CheckConstraint("daily_new_cards BETWEEN 0 AND 500", name="daily_new_cards"),
        CheckConstraint("daily_review_limit BETWEEN 0 AND 2000", name="daily_review_limit"),
        CheckConstraint("theme IN ('light','dark','system')", name="theme"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    target_language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    explanation_language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    show_hindi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cefr_level: Mapped[str] = mapped_column(String(2), default="A2", nullable=False)
    daily_new_cards: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    daily_review_limit: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Berlin", nullable=False)
    theme: Mapped[str] = mapped_column(String(8), default="system", nullable=False)

    user: Mapped[User] = relationship(back_populates="preferences")
