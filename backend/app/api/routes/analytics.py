from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.analytics import DashboardOut
from app.services import analytics as svc

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: CurrentUser, db: DB) -> DashboardOut:
    return svc.dashboard(db, user)
