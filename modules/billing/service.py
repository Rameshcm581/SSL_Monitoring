import logging
from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from configs import Configuration
from modules.billing.models import Subscriptions
from modules.users import service as users_service

logger = logging.getLogger(__name__)
stripe.api_key = Configuration.STRIPE_SECRET_KEY


async def create_checkout_session(db: AsyncSession, user_id: str, success_url: str,
                                   cancel_url: str) -> str:
    user = await users_service.get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user.email,
        line_items=[{"price": Configuration.STRIPE_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user_id)},
    )
    return session.url


async def get_subscription_status(db: AsyncSession, user_id: str) -> str:
    result = await db.execute(
        select(Subscriptions).where(Subscriptions.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    return sub.status if sub else "inactive"


async def handle_webhook_event(db: AsyncSession, event: dict) -> None:
    """Called from the webhook controller after signature verification."""
    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user_id = data["metadata"]["user_id"]
        result = await db.execute(select(Subscriptions).where(Subscriptions.user_id == user_id))
        sub = result.scalar_one_or_none()
        if not sub:
            sub = Subscriptions(user_id=user_id)
            db.add(sub)
        sub.stripe_customer_id = data["customer"]
        sub.stripe_subscription_id = data["subscription"]
        sub.status = "active"
        await db.commit()

    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        stripe_sub_id = data["id"]
        result = await db.execute(
            select(Subscriptions).where(Subscriptions.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = data["status"]
            if data.get("current_period_end"):
                sub.current_period_end = datetime.fromtimestamp(
                    data["current_period_end"], tz=timezone.utc
                )
            await db.commit()
