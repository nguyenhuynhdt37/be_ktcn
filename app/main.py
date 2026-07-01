from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import setup_exception_handlers
from app.core.logger import setup_logging
from app.modules.auth.router import router as auth_router, users_router
from app.modules.audit.router import audit_router
from app.modules.health.router import router as health_router
from app.modules.media.router import media_router
from app.modules.menu.router import menu_router
from app.modules.category.routers import admin_router as category_admin_router, portal_router as category_portal_router
from app.modules.article.router import router as article_router
from app.modules.tag.router import router as tag_router
from app.modules.faculty_staff.router import positions_router, departments_router, staffs_router
from app.modules.banner.router import banners_router
from app.modules.language.router import admin_router as language_admin_router, portal_router as language_portal_router
from app.modules.translation import translation_router, translation_service
from app.shared.redis import close_redis, init_redis

# Import all models to ensure they are registered on Base.metadata and prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.menu.models import Menu, MenuItem
from app.modules.category.models import Category
from app.modules.article.models import Article
from app.modules.tag.models import Tag
from app.modules.faculty_staff.models import Department, Position, Staff
from app.modules.banner.models import Banner
from app.modules.language.models import Language

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

    # Startup: Warmup translation model (NLLB-200)
    translation_service.warmup()
    
    # Startup: Launch daily AI models sync task at 00:00
    import asyncio
    from app.modules.article.tasks import start_article_scheduler_task
    asyncio.create_task(start_article_scheduler_task())
    
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

app.include_router(media_router, prefix=f"{settings.API_V1_STR}/media", tags=["media"])
app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/audit-logs", tags=["audit"])
app.include_router(menu_router, prefix=f"{settings.API_V1_STR}/menus", tags=["menus"])
app.include_router(category_admin_router, prefix=f"{settings.API_V1_STR}/admin/categories", tags=["admin-categories"])
app.include_router(category_portal_router, prefix=f"{settings.API_V1_STR}/portal/categories", tags=["portal-categories"])
app.include_router(article_router, prefix=f"{settings.API_V1_STR}/articles", tags=["articles"])
app.include_router(tag_router, prefix=f"{settings.API_V1_STR}/tags", tags=["tags"])
app.include_router(positions_router, prefix=f"{settings.API_V1_STR}/positions", tags=["positions"])
app.include_router(departments_router, prefix=f"{settings.API_V1_STR}/departments", tags=["departments"])
app.include_router(staffs_router, prefix=f"{settings.API_V1_STR}/staffs", tags=["staffs"])
app.include_router(banners_router, prefix=f"{settings.API_V1_STR}/banners", tags=["banners"])
app.include_router(language_admin_router, prefix=f"{settings.API_V1_STR}/languages", tags=["languages"])
app.include_router(language_portal_router, prefix=f"{settings.API_V1_STR}/portal/languages", tags=["portal-languages"])
app.include_router(translation_router, prefix=f"{settings.API_V1_STR}/translation", tags=["translation"])
