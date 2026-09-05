from core.logging_config import configure_logging
configure_logging()  # must run before any module that logs is imported

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from configs import Configuration
from core.database import Base, engine
from core.scheduler import start_scheduler, stop_scheduler

from modules.auth.routes import router as auth_router
from modules.sites.routes import router as sites_router
from modules.checks.routes import router as checks_router
from modules.billing.routes import router as billing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
        await app.state.http_client.aclose()
        await engine.dispose()


app = FastAPI(title="Uptime Monitor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Configuration.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)      # /api/auth/*
app.include_router(sites_router)     # /api/sites/*
app.include_router(checks_router)    # /api/checks/*
app.include_router(billing_router)   # /api/billing/*
