from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.formatting_profile import FormattingProfile
from app.models.user import User
from app.pipeline.rules import FormattingRules
from app.services.profiles import get_system_default_profile, get_user_profile

router = APIRouter(prefix="/profiles", tags=["profiles"])

USER_PROFILE_NAME = "My settings"


@router.get("/me", response_model=FormattingRules)
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FormattingRules:
    profile = await get_user_profile(user, db) or await get_system_default_profile(db)
    return FormattingRules.model_validate(profile.rules if profile else {})


@router.put("/me", response_model=FormattingRules)
async def update_my_profile(
    rules: FormattingRules,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FormattingRules:
    profile = await get_user_profile(user, db)
    if profile is None:
        profile = FormattingProfile(owner_id=user.id, name=USER_PROFILE_NAME, rules={})
        db.add(profile)

    profile.rules = rules.model_dump()
    await db.commit()
    await db.refresh(profile)

    return FormattingRules.model_validate(profile.rules)
