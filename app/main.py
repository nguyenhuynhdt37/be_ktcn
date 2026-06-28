from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import setup_exception_handlers
from app.core.logger import setup_logging
from app.modules.auth.router import router as auth_router, users_router, roles_router, permissions_router
from app.modules.audit.router import audit_router
from app.modules.health.router import router as health_router
from app.modules.media.router import media_router
from app.modules.menu.router import menu_router
from app.modules.category.router import category_router
from app.modules.ai.router import ai_router
from app.shared.redis import close_redis, init_redis

# Initialize global logging configuration
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle of the FastAPI application.
    Executes tasks during startup and teardown phases.
    """
    # Startup: Initialize Redis pool
    init_redis()
    
    # Startup: Launch daily AI models sync task at 00:00
    import asyncio
    from app.modules.ai.tasks import start_daily_ai_sync_task
    asyncio.create_task(start_daily_ai_sync_task())
    
    yield
    # Shutdown: Clean up connections
    await close_redis()
    await engine.dispose()  # Close SQLAlchemy engine connection pool


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CMS and Portal backend for University Website",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)

# Configure CORS (Cross-Origin Resource Sharing)
if settings.ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
elif settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Configure global exception interceptors
setup_exception_handlers(app)

# Register API Routers
# /health check is placed at the root level for easy monitoring access
app.include_router(health_router)

# All standard modules are prefixed with /api/v1
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(roles_router, prefix=f"{settings.API_V1_STR}/roles", tags=["roles"])
app.include_router(permissions_router, prefix=f"{settings.API_V1_STR}/permissions", tags=["permissions"])
app.include_router(media_router, prefix=f"{settings.API_V1_STR}/media", tags=["media"])
app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/audit-logs", tags=["audit"])
app.include_router(menu_router, prefix=f"{settings.API_V1_STR}/menus", tags=["menus"])
app.include_router(category_router, prefix=f"{settings.API_V1_STR}/categories", tags=["categories"])
app.include_router(ai_router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai"])

