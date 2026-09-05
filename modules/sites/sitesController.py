import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from modules.sites import service as sites_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_sites(db: AsyncSession = Depends(get_db),
                      claims: dict = Depends(get_current_user)):
    try:
        sites = await sites_service.list_sites_for_user(db, claims["user_id"])
        return {"data": sites}
    except Exception as exc:
        logger.error("list_sites | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("", status_code=201)
async def create_site(request: Request, db: AsyncSession = Depends(get_db),
                       claims: dict = Depends(get_current_user)):
    try:
        payload = await request.json()
        name = (payload.get("name") or "").strip()
        url = (payload.get("url") or "").strip()
        if not name or not url:
            raise HTTPException(status_code=400, detail="name and url are required")
        if not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="url must start with http:// or https://")

        site = await sites_service.create_site(db, claims["user_id"], name, url)
        return {"status": "success", "data": site}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("create_site | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{site_id}")
async def delete_site(site_id: str, db: AsyncSession = Depends(get_db),
                       claims: dict = Depends(get_current_user)):
    try:
        deleted = await sites_service.soft_delete_site(db, site_id, claims["user_id"])
        if not deleted:
            raise HTTPException(status_code=404, detail="Site not found")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("delete_site | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
