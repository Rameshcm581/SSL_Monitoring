import logging
import socket
import ssl
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from modules.checks.models import StatusChecks
from modules.sites import service as sites_service
from modules.alerts import service as alerts_service

logger = logging.getLogger(__name__)


async def probe_http(url: str) -> dict:
    """External call — real ping to the monitored site. Uses a fresh short-lived
    client per probe since target hosts vary (not the shared app.state client,
    which is reserved for calls to our OWN third-party APIs)."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        status = "up" if resp.status_code < 500 else "down"
        return {"status": status, "response_time_ms": elapsed_ms,
                "http_status_code": resp.status_code}
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        logger.warning("probe_http failed | url=%s | %s", url, exc)
        return {"status": "down", "response_time_ms": None, "http_status_code": None}


def probe_ssl_expiry(url: str):
    """Blocking socket call — run in scheduler thread, not the event loop."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        expiry_str = cert["notAfter"]
        expiry_dt = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
        return expiry_dt.date()
    except Exception as exc:
        logger.warning("probe_ssl_expiry failed | url=%s | %s", url, exc)
        return None


async def run_http_check_cycle(db: AsyncSession) -> None:
    """Scheduler job: check every active site, log result, update cached status,
    trigger alerts on state change."""
    sites = await sites_service.list_all_active_sites(db)
    for site in sites:
        result = await probe_http(site.url)
        check = StatusChecks(site_id=site.id, **result)
        db.add(check)

        prev_status = site.current_status
        await sites_service.update_status(db, str(site.id), result["status"])

        if prev_status != "down" and result["status"] == "down":
            await alerts_service.send_down_alert(db, site)
        elif prev_status == "down" and result["status"] == "up":
            await alerts_service.send_recovery_alert(db, site)

    await db.commit()


async def run_ssl_check_cycle(db: AsyncSession) -> None:
    """Scheduler job: daily SSL expiry check, alert at 30/14/7 day thresholds."""
    sites = await sites_service.list_all_active_sites(db)
    for site in sites:
        expiry_date = probe_ssl_expiry(site.url)
        if not expiry_date:
            continue
        await sites_service.update_ssl_expiry(db, str(site.id), expiry_date)

        days_left = (expiry_date - datetime.now(timezone.utc).date()).days
        if days_left in (30, 14, 7):
            await alerts_service.send_ssl_expiry_alert(db, site, days_left)


async def get_uptime_percent(db: AsyncSession, site_id: str, days: int = 30) -> float:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    total = await db.scalar(
        select(func.count(StatusChecks.id)).where(
            StatusChecks.site_id == site_id, StatusChecks.checked_at >= since
        )
    )
    if not total:
        return 100.0
    up = await db.scalar(
        select(func.count(StatusChecks.id)).where(
            StatusChecks.site_id == site_id,
            StatusChecks.checked_at >= since,
            StatusChecks.status == "up",
        )
    )
    return round((up / total) * 100, 2)
