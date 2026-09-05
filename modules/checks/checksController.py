import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from modules.checks import service as checks_service
from modules.sites import service as sites_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{site_id}/uptime")
async def get_uptime(site_id: str, db: AsyncSession = Depends(get_db),
                      claims: dict = Depends(get_current_user)):
    try:
        site = await sites_service.get_site(db, site_id)
        if not site or str(site.user_id) != str(claims["user_id"]):
            raise HTTPException(status_code=404, detail="Site not found")

        uptime = await checks_service.get_uptime_percent(db, site_id)
        return {"data": {"site_id": site_id, "uptime_percent": uptime}}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_uptime | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
