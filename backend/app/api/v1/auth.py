from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_client_ip
from app.core.database import get_db
from app.core.errors import AppError
from app.core.rate_limit import login_rate_limiter
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
    TokenResponse,
    TokenUser,
)
from app.services import auth_service
from app.utils.responses import success

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = get_client_ip(request)
    rl_key = f"{payload.email.lower().strip()}|{ip}"
    if not login_rate_limiter.is_allowed(rl_key):
        raise AppError(
            "RATE_LIMITED", "Too many login attempts. Please try again later.", 429
        )
    user, access, refresh = auth_service.login(db, payload.email, payload.password, ip=ip)
    db.commit()
    login_rate_limiter.reset(rl_key)
    return success(
        TokenResponse(
            access_token=access, refresh_token=refresh, user=TokenUser.model_validate(user)
        )
    )


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    access, new_refresh = auth_service.refresh_tokens(db, payload.refresh_token)
    db.commit()
    return success(TokenPairResponse(access_token=access, refresh_token=new_refresh))


@router.post("/logout")
def logout(payload: LogoutRequest, user: CurrentUser, db: Session = Depends(get_db)):
    auth_service.logout(db, payload.refresh_token, user)
    db.commit()
    return success({"revoked": True})
