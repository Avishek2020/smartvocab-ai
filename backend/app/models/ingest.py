import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPk

SOURCE_TYPES = ("pdf", "image", "text", "audio", "url", "docx", "xlsx", "txt", "epub", "youtube", "clipboard")
JOB_STATUSES = ("queued", "running", "succeeded", "failed", "cancelled")


class UploadedDocument(UUIDPk, Timestamps, Base):
    __tablename__ = "uploaded_documents"
    __table_args__ = (
        CheckConstraint(f"source_type IN {SOURCE_TYPES}", name="source_type"),
        Index("ix_uploaded_documents_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(12), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(300))
    source_url: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(String(300))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(String(64))
    page_count: Mapped[int | None] = mapped_column(Integer)
    detected_language: Mapped[str | None] = mapped_column(String(8))
    extracted_text_key: Mapped[str | None] = mapped_column(String(300))


class ExtractionJob(UUIDPk, Timestamps, Base):
    __tablename__ = "extraction_jobs"
    __table_args__ = (
        CheckConstraint(f"status IN {JOB_STATUSES}", name="status"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress"),
        Index("ix_extraction_jobs_status_created", "status", "created_at"),
        Index("ix_extraction_jobs_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("uploaded_documents.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(12), default="queued", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stage: Mapped[str | None] = mapped_column(String(40))
    options: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)   # mode, max_cards, pages, ...
    model_name: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(40))
    cards_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AudioRecording(UUIDPk, Timestamps, Base):
    __tablename__ = "audio_recordings"
    __table_args__ = (Index("ix_audio_recordings_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(300), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(60), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    purpose: Mapped[str] = mapped_column(String(20), default="vocabulary", nullable=False)  # vocabulary | tutor | pronunciation


class SpeechTranscript(UUIDPk, Timestamps, Base):
    __tablename__ = "speech_transcripts"

    recording_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_recordings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    language: Mapped[str | None] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    segments: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)  # word/segment timestamps
    provider: Mapped[str | None] = mapped_column(String(40))
    model_name: Mapped[str | None] = mapped_column(String(120))
