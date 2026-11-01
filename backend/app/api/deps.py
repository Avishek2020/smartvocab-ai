from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

DB = Annotated[Session, Depends(get_db)]


def _token_from_request(request: Request) -> str | None:
    token = request.cookies.get(get_settings().cookie_name)
    if token:
        return token
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def current_user(request: Request, db: DB) -> User:
    token = _token_from_request(request)
    if not token:
        raise AppError(401, "not_authenticated", "Please sign in")
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise AppError(401, "invalid_token", "Your session is invalid or has expired") from None
    user = db.get(User, user_id)
    if user is None or not user.is_active or user.token_version != payload.get("tv"):
        raise AppError(401, "invalid_token", "Your session is invalid or has expired")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
