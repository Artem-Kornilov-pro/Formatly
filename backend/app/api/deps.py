import uuid

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis import get_redis
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    redis_client: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token")

    user_id = await redis_client.get(f"access:{credentials.credentials}")
    if user_id is None:
        raise unauthorized

    try:
        user = await db.get(User, uuid.UUID(user_id))
    except ValueError:
        raise unauthorized from None

    if user is None:
        raise unauthorized

    return user
