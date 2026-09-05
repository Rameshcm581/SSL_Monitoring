import logging
from datetime import datetime, timedelta, timezone

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from configs import Configuration
from modules.alerts.models import AlertsSent
from modules.users import service as users_service

logger = logging.getLogger(__name__)

_DEDUP_WINDOW_HOURS = 6


async def _recently_sent(db: AsyncSession, site_id, alert_type: str) -> bool:
    since = datetime.now(timezone.utc) - timedelta(hours=_DEDUP_WINDOW_HOURS)
    result = await db.execute(
        select(AlertsSent).where(
            AlertsSent.site_id == site_id,
            AlertsSent.alert_type == alert_type,
            AlertsSent.sent_at >= since,
        )
    )
    return result.scalar_one_or_none() is not None


def _dispatch_email(to_email: str, subject: str, body: str) -> None:
    """Sync SendGrid call — fine to call directly, scheduler runs off the main
    request path so this won't block user-facing requests."""
    try:
        message = Mail(from_email=Configuration.ALERT_FROM_EMAIL, to_emails=to_email,
                        subject=subject, plain_text_content=body)
        sg = SendGridAPIClient(Configuration.SENDGRID_API_KEY)
        sg.send(message)
    except Exception as exc:
        logger.error("email dispatch failed | to=%s | %s", to_email, exc, exc_info=True)


async def send_down_alert(db: AsyncSession, site) -> None:
    if await _recently_sent(db, site.id, "down"):
        return
    alert_email = await users_service.get_alert_email(db, str(site.user_id))
    if not alert_email:
        return
    _dispatch_email(alert_email, f"{site.name} is DOWN",
                     f"{site.name} ({site.url}) failed its last check.")
    db.add(AlertsSent(site_id=site.id, alert_type="down"))
    await db.commit()


async def send_recovery_alert(db: AsyncSession, site) -> None:
    alert_email = await users_service.get_alert_email(db, str(site.user_id))
    if not alert_email:
        return
    _dispatch_email(alert_email, f"{site.name} has recovered",
                     f"{site.name} ({site.url}) is back up.")
    db.add(AlertsSent(site_id=site.id, alert_type="recovered"))
    await db.commit()


async def send_ssl_expiry_alert(db: AsyncSession, site, days_left: int) -> None:
    alert_type = f"ssl_expiring_{days_left}d"
    if await _recently_sent(db, site.id, alert_type):
        return
    alert_email = await users_service.get_alert_email(db, str(site.user_id))
    if not alert_email:
        return
    _dispatch_email(alert_email, f"{site.name} SSL cert expires in {days_left} days",
                     f"{site.name} ({site.url}) certificate expires in {days_left} days.")
    db.add(AlertsSent(site_id=site.id, alert_type=alert_type))
    await db.commit()
