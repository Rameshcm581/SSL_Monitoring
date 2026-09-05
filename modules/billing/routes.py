from fastapi import APIRouter

from modules.billing.billingController import router as billing_controller_router

router = APIRouter(prefix="/api/billing", tags=["Billing"])
router.include_router(billing_controller_router)
