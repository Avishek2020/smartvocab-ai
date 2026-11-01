from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.vocabulary import CARD_STATUSES, PARTS_OF_SPEECH

PartOfSpeech = Literal[PARTS_OF_SPEECH]  # type: ignore[valid-type]
Cefr = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class ExampleIn(BaseModel):
    sentence: str = Field(min_length=1, max_length=1000)
    translation: str | None = Field(default=None, max_length=1000)
    kind: Literal["example", "conversation", "source"] = "example"


class ExampleOut(ExampleIn):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


def _clean_list(v: list[str]) -> list[str]:
    seen, out = set(), []
    for item in v:
        s = item.strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


class CardBase(BaseModel):
    term: str = Field(min_length=1, max_length=200)
    lemma: str | None = Field(default=None, max_length=200)
    sense_key: str = Field(default="", max_length=120)
    part_of_speech: PartOfSpeech
    cefr_level: Cefr | None = None
    translations: dict[str, str] = Field(default_factory=dict)
    phonetic: str | None = Field(default=None, max_length=200)
    explanation: str | None = Field(default=None, max_length=4000)
    source_sentence: str | None = Field(default=None, max_length=2000)
    source_reference: str | None = Field(default=None, max_length=300)
    synonyms: list[str] = Field(default_factory=list, max_length=30)
    antonyms: list[str] = Field(default_factory=list, max_length=30)
    collocations: list[str] = Field(default_factory=list, max_length=30)
    common_mistakes: list[str] = Field(default_factory=list, max_length=20)
    personal_note: str | None = Field(default=None, max_length=4000)
    grammar: dict | None = None
    examples: list[ExampleIn] = Field(default_factory=list, max_length=10)

    @field_validator("term", "lemma", "sense_key")
    @classmethod
    def strip(cls, v: str | None) -> str | None:
        return v.strip() if isinstance(v, str) else v

    @field_validator("translations")
    @classmethod
    def translations_valid(cls, v: dict[str, str]) -> dict[str, str]:
        out = {k.strip().lower(): t.strip() for k, t in v.items() if t and t.strip()}
        for k in out:
            if not (2 <= len(k) <= 8):
                raise ValueError(f"invalid language code '{k}'")
        return out

    @field_validator("synonyms", "antonyms", "collocations", "common_mistakes")
    @classmethod
    def lists(cls, v: list[str]) -> list[str]:
        return _clean_list(v)


class CardCreate(CardBase):
    collection_ids: list[UUID] = Field(default_factory=list, max_length=20)


class CardUpdate(CardBase):
    status: Literal[CARD_STATUSES] | None = None  # type: ignore[valid-type]
    collection_ids: list[UUID] | None = None


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    term: str
    lemma: str
    sense_key: str
    language: str
    part_of_speech: str
    cefr_level: str | None
    translations: dict[str, str]
    phonetic: str | None
    explanation: str | None
    source_sentence: str | None
    source_reference: str | None
    synonyms: list[str]
    antonyms: list[str]
    collocations: list[str]
    common_mistakes: list[str]
    personal_note: str | None
    grammar: dict | None
    examples: list[ExampleOut]
    collection_ids: list[UUID]
    status: str
    created_via: str
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CardPage(BaseModel):
    items: list[CardOut]
    total: int
    page: int
    page_size: int


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class CollectionOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    color: str | None
    is_default: bool
    card_count: int
