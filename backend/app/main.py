from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME}...")

    # Import all domain models to register them with Base
    from app.domains import auth, sites, checks, notifications  # noqa: F401

    # Import check plugins to register them
    from app.domains.checks.plugins import http_check, dns_check, ssl_check  # noqa: F401
    from app.domains.checks.plugins import ping_check, keyword_check, port_check  # noqa: F401

    # Import notification channels to register them
    from app.domains.notifications.channels import email, webhook, slack, discord  # noqa: F401

    # Create tables if they don't exist (development only)
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Initialize and start APScheduler
    from app.core.scheduler import init_scheduler
    from app.tasks.checks import sync_check_schedules

    global scheduler
    scheduler = init_scheduler()
    scheduler.start()
    print("✅ APScheduler started")

    # Sync existing check schedules
    await sync_check_schedules()

    print("✅ Application started successfully")

    yield

    # Shutdown
    print("🛑 Shutting down application...")

    # Shutdown APScheduler
    if scheduler:
        scheduler.shutdown(wait=True)
        print("✅ APScheduler shutdown")

    await engine.dispose()
    print("✅ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-user health check monitoring system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/api/docs",
        "health": "/health",
    }


# Include domain API routers
from app.domains.auth import router as auth_router
from app.domains.sites import router as sites_router
from app.domains.checks import router as checks_router
from app.domains.notifications import router as notifications_router
from app.api.v1 import stream

app.include_router(auth_router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(sites_router, prefix=f"{settings.API_V1_PREFIX}/sites", tags=["Sites"])
app.include_router(checks_router, prefix=f"{settings.API_V1_PREFIX}/checks", tags=["Checks"])
app.include_router(notifications_router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["Notifications"])
app.include_router(stream.router, prefix=f"{settings.API_V1_PREFIX}/stream", tags=["Real-time Updates"])
