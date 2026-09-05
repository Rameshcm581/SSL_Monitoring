from fastapi import APIRouter

from modules.sites.sitesController import router as sites_controller_router

router = APIRouter(prefix="/api/sites", tags=["Sites"])
router.include_router(sites_controller_router)
