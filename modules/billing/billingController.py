import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from configs import Configuration
from core.database import get_db
from core.security import get_current_user
from modules.billing import service as billing_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/checkout")
async def checkout(request: Request, db: AsyncSession = Depends(get_db),
                    claims: dict = Depends(get_current_user)):
    try:
        payload = await request.json()
        success_url = payload.get("success_url")
        cancel_url = payload.get("cancel_url")
        if not success_url or not cancel_url:
            raise HTTPException(status_code=400,
                                 detail="success_url and cancel_url are required")

        url = await billing_service.create_checkout_session(
            db, claims["user_id"], success_url, cancel_url
        )
        return {"data": {"checkout_url": url}}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("checkout | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/status")
async def status(db: AsyncSession = Depends(get_db),
                  claims: dict = Depends(get_current_user)):
    sub_status = await billing_service.get_subscription_status(db, claims["user_id"])
    return {"data": {"status": sub_status}}


@router.post("/webhook")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, Configuration.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning("webhook signature invalid | %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    try:
        await billing_service.handle_webhook_event(db, event)
        return {"status": "success"}
    except Exception as exc:
        logger.error("webhook handling | 500 | %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc
