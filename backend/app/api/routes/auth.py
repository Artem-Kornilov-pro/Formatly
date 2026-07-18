import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.redis import get_redis
from app.core.security import generate_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _user_out(user: User) -> UserOut:
    return UserOut(id=str(user.id), email=user.email)


async def _issue_tokens(user_id: str, redis_client: redis.Redis) -> TokenPair:
    access_token = generate_token()
    refresh_token = generate_token()
    await redis_client.set(f"access:{access_token}", user_id, ex=settings.access_token_ttl_seconds)
    await redis_client.set(f"refresh:{refresh_token}", user_id, ex=settings.refresh_token_ttl_seconds)
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserOut:
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_out(user)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> TokenPair:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    return await _issue_tokens(str(user.id), redis_client)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshRequest,
    redis_client: redis.Redis = Depends(get_redis),
) -> TokenPair:
    key = f"refresh:{payload.refresh_token}"
    user_id = await redis_client.get(key)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    await redis_client.delete(key)
    return await _issue_tokens(user_id, redis_client)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    redis_client: redis.Redis = Depends(get_redis),
) -> None:
    await redis_client.delete(f"refresh:{payload.refresh_token}")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)
