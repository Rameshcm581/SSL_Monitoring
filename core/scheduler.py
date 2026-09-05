import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from configs import Configuration
from core.database import AsyncSessionLocal
from modules.checks import service as checks_service

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _run_http_checks():
    async with AsyncSessionLocal() as db:
        try:
            await checks_service.run_http_check_cycle(db)
        except Exception as exc:
            logger.error("http check cycle failed | %s", exc, exc_info=True)


async def _run_ssl_checks():
    async with AsyncSessionLocal() as db:
        try:
            await checks_service.run_ssl_check_cycle(db)
        except Exception as exc:
            logger.error("ssl check cycle failed | %s", exc, exc_info=True)


def start_scheduler():
    scheduler.add_job(_run_http_checks, "interval",
                       minutes=Configuration.CHECK_INTERVAL_MINUTES,
                       id="http_checks", replace_existing=True)
    scheduler.add_job(_run_ssl_checks, "interval",
                       hours=Configuration.SSL_CHECK_INTERVAL_HOURS,
                       id="ssl_checks", replace_existing=True)
    scheduler.start()
    logger.info("scheduler started | http_interval=%smin | ssl_interval=%shr",
                Configuration.CHECK_INTERVAL_MINUTES, Configuration.SSL_CHECK_INTERVAL_HOURS)


def stop_scheduler():
    scheduler.shutdown(wait=False)
