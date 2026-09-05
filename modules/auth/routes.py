from fastapi import APIRouter, Depends

from core.security import get_current_user
from modules.auth.authController import router as auth_controller_router

router = APIRouter(prefix="/api/auth", tags=["Auth"])
router.include_router(auth_controller_router)


@router.post("/logout")
async def logout(_=Depends(get_current_user)):
    return {"status": "success"}


@router.get("/health")
async def health():
    return {"status": "ok"}
