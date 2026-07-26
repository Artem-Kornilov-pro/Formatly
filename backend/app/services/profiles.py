from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.formatting_profile import FormattingProfile
from app.models.user import User


async def get_system_default_profile(db: AsyncSession) -> FormattingProfile | None:
    return await db.scalar(
        select(FormattingProfile)
        .where(FormattingProfile.owner_id.is_(None))
        .order_by(FormattingProfile.created_at)
        .limit(1)
    )


async def get_user_profile(user: User, db: AsyncSession) -> FormattingProfile | None:
    return await db.scalar(select(FormattingProfile).where(FormattingProfile.owner_id == user.id))


async def resolve_default_profile(user: User, db: AsyncSession) -> FormattingProfile | None:
    """The profile a job should use when none is explicitly requested.

    Prefers the user's own saved settings over the system default.
    """
    return await get_user_profile(user, db) or await get_system_default_profile(db)
