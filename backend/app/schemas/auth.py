from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import CEFR_LEVELS


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=72)
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("password")
    @classmethod
    def strength(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password is too long")
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError("password must contain letters and at least one digit")
        return v

    @field_validator("display_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("display name is required")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class PreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_language: str
    explanation_language: str
    show_hindi: bool
    cefr_level: str
    daily_new_cards: int
    daily_review_limit: int
    timezone: str
    theme: str


class PreferencesUpdate(BaseModel):
    explanation_language: str | None = Field(default=None, min_length=2, max_length=8)
    show_hindi: bool | None = None
    cefr_level: str | None = None
    daily_new_cards: int | None = Field(default=None, ge=0, le=500)
    daily_review_limit: int | None = Field(default=None, ge=0, le=2000)
    timezone: str | None = Field(default=None, max_length=64)
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")

    @field_validator("cefr_level")
    @classmethod
    def cefr(cls, v: str | None) -> str | None:
        if v is not None and v not in CEFR_LEVELS:
            raise ValueError(f"cefr_level must be one of {', '.join(CEFR_LEVELS)}")
        return v


class UserOut(BaseModel):
    id: UUID
    email: str
    display_name: str
    preferences: PreferencesOut
