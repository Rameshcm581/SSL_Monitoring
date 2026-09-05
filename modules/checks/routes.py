from fastapi import APIRouter

from modules.checks.checksController import router as checks_controller_router

router = APIRouter(prefix="/api/checks", tags=["Checks"])
router.include_router(checks_controller_router)
