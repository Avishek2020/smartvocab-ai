from fastapi import APIRouter, Depends, Response, status

from app.api.deps import DB, CurrentUser
from app.core.config import get_settings
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, UserOut
from app.services import users as svc

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session(response: Response, user: User) -> None:
    s = get_settings()
    response.set_cookie(
        s.cookie_name, create_access_token(user.id, user.token_version),
        max_age=s.access_token_minutes * 60, httponly=True, secure=s.cookie_secure,
        samesite=s.cookie_samesite, path="/",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(rate_limit("register"))])
def register(data: RegisterIn, response: Response, db: DB) -> UserOut:
    user = svc.register(db, data)
    _set_session(response, user)
    return svc.user_out(db, user)


@router.post("/login", response_model=UserOut, dependencies=[Depends(rate_limit("login"))])
def login(data: LoginIn, response: Response, db: DB) -> UserOut:
    user = svc.authenticate(db, data.email, data.password)
    _set_session(response, user)
    return svc.user_out(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user: CurrentUser, response: Response, db: DB) -> Response:
    svc.revoke_sessions(db, user)  # invalidates this and every other token for the user
    s = get_settings()
    response.delete_cookie(s.cookie_name, path="/", httponly=True, secure=s.cookie_secure, samesite=s.cookie_samesite)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
