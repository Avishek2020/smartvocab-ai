from fastapi import APIRouter, Response, status

from app.api.deps import DB, CurrentUser
from app.core.config import get_settings
from app.schemas.auth import PreferencesOut, PreferencesUpdate, UserOut
from app.services import users as svc

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, db: DB) -> UserOut:
    return svc.user_out(db, user)


@router.patch("/me/preferences", response_model=PreferencesOut)
def update_preferences(data: PreferencesUpdate, user: CurrentUser, db: DB) -> PreferencesOut:
    return svc.preferences_out(db, svc.update_preferences(db, user, data))


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: CurrentUser, db: DB, response: Response) -> Response:
    svc.delete_account(db, user)
    s = get_settings()
    response.delete_cookie(s.cookie_name, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
