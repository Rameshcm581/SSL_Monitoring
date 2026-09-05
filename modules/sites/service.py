from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.sites.models import Sites


async def create_site(db: AsyncSession, user_id: str, name: str, url: str) -> Sites:
    site = Sites(user_id=user_id, name=name, url=url)
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


async def list_sites_for_user(db: AsyncSession, user_id: str) -> Sequence[Sites]:
    result = await db.execute(
        select(Sites).where(Sites.user_id == user_id, Sites.is_active.is_(True))
    )
    return result.scalars().all()


async def get_site(db: AsyncSession, site_id: str) -> Optional[Sites]:
    result = await db.execute(select(Sites).where(Sites.id == site_id))
    return result.scalar_one_or_none()


async def list_all_active_sites(db: AsyncSession) -> Sequence[Sites]:
    """In-process API used by the checks module scheduler."""
    result = await db.execute(select(Sites).where(Sites.is_active.is_(True)))
    return result.scalars().all()


async def update_status(db: AsyncSession, site_id: str, status: str) -> None:
    site = await get_site(db, site_id)
    if site:
        site.current_status = status
        await db.commit()


async def update_ssl_expiry(db: AsyncSession, site_id: str, expiry_date) -> None:
    site = await get_site(db, site_id)
    if site:
        site.ssl_expiry_date = expiry_date
        await db.commit()


async def soft_delete_site(db: AsyncSession, site_id: str, user_id: str) -> bool:
    site = await get_site(db, site_id)
    if not site or str(site.user_id) != str(user_id):
        return False
    site.is_active = False
    await db.commit()
    return True
