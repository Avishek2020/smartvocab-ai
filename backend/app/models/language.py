from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPk


class Language(UUIDPk, Timestamps, Base):
    """A supported language. New languages are rows (plus a grammar plugin), not schema changes."""

    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)  # ISO 639-1, e.g. "de"
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # English name
    native_name: Mapped[str] = mapped_column(String(64), nullable=False)
    can_learn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_explain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tts_locale: Mapped[str | None] = mapped_column(String(16))  # e.g. "de-DE"
