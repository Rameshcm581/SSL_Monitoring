import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from modules.auth import service as auth_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201)
async def register(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        if not email or not password:
            raise HTTPException(status_code=400, detail="email and password are required")
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="password must be at least 8 characters")

        result = await auth_service.register(db, email, password)
        return {"status": "success", **result}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("register | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/login", status_code=200)
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        if not email or not password:
            raise HTTPException(status_code=400, detail="email and password are required")

        result = await auth_service.login(db, email, password)
        return {"status": "success", **result}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("login | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
