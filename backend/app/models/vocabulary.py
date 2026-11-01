import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, Timestamps, UUIDPk

PARTS_OF_SPEECH = (
    "noun", "verb", "adjective", "adverb", "preposition", "conjunction", "pronoun",
    "article", "numeral", "interjection", "particle", "phrase", "idiom", "other",
)
CARD_STATUSES = ("draft", "new", "learning", "review", "mastered", "suspended")


class VocabularyCard(UUIDPk, Timestamps, Base):
    __tablename__ = "vocabulary_cards"
    __table_args__ = (
        # One card per lemma *and sense* per language per user (Bank=bench vs Bank=bank are two cards).
        UniqueConstraint("user_id", "language_id", "lemma", "sense_key", name="uq_vocabulary_cards_user_lemma_sense"),
        CheckConstraint(f"part_of_speech IN {PARTS_OF_SPEECH}", name="part_of_speech"),
        CheckConstraint(f"status IN {CARD_STATUSES}", name="status"),
        CheckConstraint("cefr_level IS NULL OR cefr_level IN ('A1','A2','B1','B2','C1','C2')", name="cefr_level"),
        CheckConstraint("ease_factor >= 1.3", name="ease_factor"),
        Index("ix_vocabulary_cards_user_due", "user_id", "due_at"),
        Index("ix_vocabulary_cards_user_status", "user_id", "status"),
        Index("ix_vocabulary_cards_user_created", "user_id", "created_at"),
        Index("ix_vocabulary_cards_translations", "translations", postgresql_using="gin"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False)

    term: Mapped[str] = mapped_column(String(200), nullable=False)       # as written, e.g. "vereinbart"
    lemma: Mapped[str] = mapped_column(String(200), nullable=False)      # dictionary form, e.g. "vereinbaren"
    sense_key: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    part_of_speech: Mapped[str] = mapped_column(String(16), nullable=False)
    cefr_level: Mapped[str | None] = mapped_column(String(2))
    # {"en": "to arrange", "hi": "तय करना"} — keyed by explanation-language code.
    translations: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    phonetic: Mapped[str | None] = mapped_column(String(200))
    explanation: Mapped[str | None] = mapped_column(Text)
    source_sentence: Mapped[str | None] = mapped_column(Text)
    source_reference: Mapped[str | None] = mapped_column(String(300))   # "p. 12", URL, timestamp
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_documents.id", ondelete="SET NULL")
    )
    synonyms: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    antonyms: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    collocations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    common_mistakes: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    personal_note: Mapped[str | None] = mapped_column(Text)
    audio_key: Mapped[str | None] = mapped_column(String(300))           # object-storage key
    image_key: Mapped[str | None] = mapped_column(String(300))
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    created_via: Mapped[str] = mapped_column(String(16), default="manual", nullable=False)

    # Scheduling state (SM-2 starting values; history lives in review_history)
    status: Mapped[str] = mapped_column(String(12), default="new", nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    examples: Mapped[list["VocabularyExample"]] = relationship(
        back_populates="card", cascade="all, delete-orphan", passive_deletes=True, order_by="VocabularyExample.position"
    )
    grammar: Mapped["VocabularyGrammar | None"] = relationship(
        back_populates="card", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class VocabularyExample(UUIDPk, Timestamps, Base):
    __tablename__ = "vocabulary_examples"
    __table_args__ = (Index("ix_vocabulary_examples_card", "card_id", "position"),)

    card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vocabulary_cards.id", ondelete="CASCADE"), nullable=False)
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    translation: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(16), default="example", nullable=False)  # example | conversation | source
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    card: Mapped[VocabularyCard] = relationship(back_populates="examples")


class VocabularyGrammar(Timestamps, Base):
    """Language-specific grammar as validated JSON. For German, validated by app.grammar.de models."""

    __tablename__ = "vocabulary_grammar"

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary_cards.id", ondelete="CASCADE"), primary_key=True
    )
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    card: Mapped[VocabularyCard] = relationship(back_populates="grammar")


class VocabularyCollection(UUIDPk, Timestamps, Base):
    __tablename__ = "vocabulary_collections"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_vocabulary_collections_user_name"),
        Index("ix_vocabulary_collections_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    color: Mapped[str | None] = mapped_column(String(16))


class CollectionCard(Base):
    __tablename__ = "collection_cards"
    __table_args__ = (Index("ix_collection_cards_card", "card_id"),)

    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary_collections.id", ondelete="CASCADE"), primary_key=True
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vocabulary_cards.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
