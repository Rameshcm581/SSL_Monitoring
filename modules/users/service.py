from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.models import Users


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[Users]:
    result = await db.execute(select(Users).where(Users.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[Users]:
    result = await db.execute(select(Users).where(Users.id == user_id))
    return result.scalar_one_or_none()


async def get_alert_email(db: AsyncSession, user_id: str) -> Optional[str]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    return user.alert_email or user.email
