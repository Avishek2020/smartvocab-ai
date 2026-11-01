from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models import Language, User, UserPreferences, VocabularyCollection
from app.schemas.auth import PreferencesOut, PreferencesUpdate, RegisterIn, UserOut

DEFAULT_COLLECTIONS: list[tuple[str, str]] = [
    ("German A1", "Beginner vocabulary"),
    ("German A2", "Elementary vocabulary"),
    ("German B1", "Intermediate vocabulary"),
    ("German B2", "Upper-intermediate vocabulary"),
    ("German C1", "Advanced vocabulary"),
    ("German C2", "Proficiency vocabulary"),
    ("Business German", "Meetings, email, negotiation"),
    ("Technical German", "Engineering, IT, manufacturing"),
    ("Academic German", "University and research language"),
    ("Daily Conversation", "Everyday expressions"),
    ("Job Interview Preparation", "Vocabulary for applications and interviews"),
    ("Exam Preparation", "Goethe, telc, TestDaF, DTB"),
]


def language_by_code(db: Session, code: str) -> Language:
    lang = db.scalar(select(Language).where(Language.code == code))
    if lang is None:
        raise AppError(422, "unknown_language", f"Language '{code}' is not supported")
    return lang


def register(db: Session, data: RegisterIn) -> User:
    german = language_by_code(db, "de")
    english = language_by_code(db, "en")
    user = User(email=data.email.lower(), password_hash=hash_password(data.password), display_name=data.display_name)
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "email_taken", "An account with this email already exists") from None
    db.add(UserPreferences(user_id=user.id, target_language_id=german.id, explanation_language_id=english.id))
    for name, desc in DEFAULT_COLLECTIONS:
        db.add(VocabularyCollection(user_id=user.id, language_id=german.id, name=name, description=desc, is_default=True))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        # Spend comparable time to avoid user enumeration via timing.
        verify_password(password, "$2b$12$C6UzMDM.H6dfI/f/IKcEeO5QwOSnz0VrEXhP1Nd0Aky5nYqC4Aqa6")
        raise AppError(401, "invalid_credentials", "Email or password is incorrect")
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise AppError(401, "invalid_credentials", "Email or password is incorrect")
    return user


def revoke_sessions(db: Session, user: User) -> None:
    user.token_version += 1
    db.commit()


def delete_account(db: Session, user: User) -> None:
    db.delete(user)  # every user-owned table cascades ON DELETE
    db.commit()


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def preferences_out(db: Session, prefs: UserPreferences) -> PreferencesOut:
    target = db.get(Language, prefs.target_language_id)
    explain = db.get(Language, prefs.explanation_language_id)
    return PreferencesOut(
        target_language=target.code, explanation_language=explain.code, show_hindi=prefs.show_hindi,
        cefr_level=prefs.cefr_level, daily_new_cards=prefs.daily_new_cards,
        daily_review_limit=prefs.daily_review_limit, timezone=prefs.timezone, theme=prefs.theme,
    )


def user_out(db: Session, user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name,
                   preferences=preferences_out(db, user.preferences))


def update_preferences(db: Session, user: User, data: PreferencesUpdate) -> UserPreferences:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    prefs = user.preferences
    patch = data.model_dump(exclude_unset=True)
    if "explanation_language" in patch:
        lang = language_by_code(db, patch.pop("explanation_language"))
        if not lang.can_explain:
            raise AppError(422, "unsupported_language", f"'{lang.code}' is not available as explanation language")
        prefs.explanation_language_id = lang.id
    if "timezone" in patch:
        try:
            ZoneInfo(patch["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            raise AppError(422, "invalid_timezone", "Unknown timezone") from None
    for k, v in patch.items():
        setattr(prefs, k, v)
    db.commit()
    db.refresh(prefs)
    return prefs
