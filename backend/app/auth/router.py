import secrets

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.auth import service
from app.auth.dependencies import get_current_user
from app.auth.schemas import UserResponse
from app.config.settings import get_settings
from app.core.exceptions import UnauthorizedError
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login():
    settings = get_settings()
    state = service.generate_oauth_state()
    response = RedirectResponse(url=service.get_google_login_url(state))
    response.set_cookie(
        "oauth_state",
        state,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=600,
        path="/api/v1/auth",
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()

    if error or not code:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=access_denied")

    expected_state = request.cookies.get("oauth_state")
    if not expected_state or not state or not secrets.compare_digest(expected_state, state):
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=invalid_state")

    try:
        token_data = await service.exchange_google_code(code)
        google_user = await service.get_google_userinfo(token_data["access_token"])
    except Exception:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    user = await service.get_or_create_user(db, google_user)
    access_token = service.create_access_token(str(user.id), user.email, user.role)
    refresh_token = await service.create_refresh_token(db, user.id)
    await db.commit()

    is_prod = settings.ENVIRONMENT == "production"
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/callback")
    response.delete_cookie("oauth_state", path="/api/v1/auth")
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/api/v1/auth",
    )
    return response


@router.post("/refresh")
async def refresh_tokens(request: Request, db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise UnauthorizedError("No refresh token")

    try:
        refresh = await service.verify_refresh_token(db, raw_token)
    except ValueError:
        raise UnauthorizedError("Invalid or expired refresh token")

    user = await db.get(User, refresh.user_id)
    if not user or user.is_deleted:
        raise UnauthorizedError("User not found")

    refresh.revoked = True
    new_access = service.create_access_token(str(user.id), user.email, user.role)
    new_refresh = await service.create_refresh_token(db, user.id)
    await db.commit()

    is_prod = settings.ENVIRONMENT == "production"
    response = JSONResponse(content={"status": "refreshed"})
    response.set_cookie(
        "access_token",
        new_access,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        new_refresh,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path="/api/v1/auth",
    )
    return response


@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    raw_token = request.cookies.get("refresh_token")
    if raw_token:
        await service.revoke_refresh_token(db, raw_token)
        await db.commit()

    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return response


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user
