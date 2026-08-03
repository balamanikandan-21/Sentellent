from fastapi import Depends, Request
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.auth.service import verify_access_token
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise UnauthorizedError()

    try:
        payload = verify_access_token(token)
    except JWTError:
        raise UnauthorizedError("Invalid or expired access token")

    result = await db.execute(
        select(User).where(User.id == payload["sub"], User.is_deleted == False)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("User not found")

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = verify_access_token(token)
    except JWTError:
        return None

    result = await db.execute(
        select(User).where(User.id == payload["sub"], User.is_deleted == False)  # noqa: E712
    )
    return result.scalar_one_or_none()


def require_role(*roles: str):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"Role '{user.role}' not authorized")
        return user

    return dependency
