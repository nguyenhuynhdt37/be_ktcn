from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import setup_exception_handlers
from app.core.logger import setup_logging
from app.modules.auth.router import router as auth_router, users_router
from app.modules.audit.routers import admin_router as audit_router
from app.modules.health.routers import portal_router as health_router
from app.modules.media.routers import admin_router as media_admin_router
from app.modules.menu.routers import admin_router as menu_admin_router, portal_router as menu_portal_router
from app.modules.category.routers import admin_router as category_admin_router, portal_router as category_portal_router
from app.modules.article.routers.admin import router as article_admin_router
from app.modules.article.routers.portal import router as article_portal_router
from app.modules.tag.routers.admin import router as tag_admin_router
from app.modules.tag.routers.portal import router as tag_portal_router
from app.modules.department.routers import department_admin_router, department_portal_router
from app.modules.position.routers import position_admin_router, position_portal_router
from app.modules.staff.routers import staff_admin_router, staff_portal_router
from app.modules.academic_title.routers import admin_router as academic_title_admin_router, portal_router as academic_title_portal_router
from app.modules.degree.routers import admin_router as degree_admin_router, portal_router as degree_portal_router
from app.modules.banner.routers import admin_router as banner_admin_router, portal_router as banner_portal_router
from app.modules.language.routers import admin_router as language_admin_router, portal_router as language_portal_router
from app.modules.translation import translation_router, translation_service
from app.modules.ai_hub.routers import ai_hub_router
from app.modules.auth.routers.profile import router as profile_router
from app.modules.search.router import router as search_router

from app.shared.redis import close_redis, init_redis

# Import all models to ensure they are registered on Base.metadata and prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.menu.models import Menu, MenuItem
from app.modules.category.models import Category, CategoryTranslation
from app.modules.article.models import Article
from app.modules.tag.models import Tag
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.position.models import Position, PositionTranslation
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.banner.models import Banner
from app.modules.language.models import Language
from app.modules.ai_hub.models import AIRequestLog


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
app.include_router(profile_router, prefix=f"{settings.API_V1_STR}/admin/profile", tags=["admin-profile"])

app.include_router(media_admin_router, prefix=f"{settings.API_V1_STR}/admin/media", tags=["admin-media"])
app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/admin/audit-logs", tags=["admin-audit-logs"])
app.include_router(menu_admin_router, prefix=f"{settings.API_V1_STR}/admin/menus", tags=["admin-menus"])
app.include_router(menu_portal_router, prefix=f"{settings.API_V1_STR}/portal/menus", tags=["portal-menus"])
app.include_router(category_admin_router, prefix=f"{settings.API_V1_STR}/admin/categories", tags=["admin-categories"])
app.include_router(category_portal_router, prefix=f"{settings.API_V1_STR}/portal/categories", tags=["portal-categories"])
app.include_router(article_admin_router, prefix=f"{settings.API_V1_STR}/admin/articles", tags=["admin-articles"])
app.include_router(article_portal_router, prefix=f"{settings.API_V1_STR}/portal/articles", tags=["portal-articles"])
app.include_router(tag_admin_router, prefix=f"{settings.API_V1_STR}/admin/tags", tags=["admin-tags"])
app.include_router(tag_portal_router, prefix=f"{settings.API_V1_STR}/portal/tags", tags=["portal-tags"])
app.include_router(department_admin_router, prefix=f"{settings.API_V1_STR}/admin/departments", tags=["admin-departments"])
app.include_router(department_portal_router, prefix=f"{settings.API_V1_STR}/portal/departments", tags=["portal-departments"])
app.include_router(position_admin_router, prefix=f"{settings.API_V1_STR}/admin/positions", tags=["admin-positions"])
app.include_router(position_portal_router, prefix=f"{settings.API_V1_STR}/portal/positions", tags=["portal-positions"])
app.include_router(staff_admin_router, prefix=f"{settings.API_V1_STR}/admin/staffs", tags=["admin-staffs"])
app.include_router(staff_portal_router, prefix=f"{settings.API_V1_STR}/portal/staffs", tags=["portal-staffs"])
app.include_router(academic_title_admin_router, prefix=f"{settings.API_V1_STR}/admin/academic-titles", tags=["admin-academic-titles"])
app.include_router(academic_title_portal_router, prefix=f"{settings.API_V1_STR}/portal/academic-titles", tags=["portal-academic-titles"])
app.include_router(degree_admin_router, prefix=f"{settings.API_V1_STR}/admin/degrees", tags=["admin-degrees"])
app.include_router(degree_portal_router, prefix=f"{settings.API_V1_STR}/portal/degrees", tags=["portal-degrees"])
app.include_router(banner_admin_router, prefix=f"{settings.API_V1_STR}/admin/banners", tags=["admin-banners"])
app.include_router(banner_portal_router, prefix=f"{settings.API_V1_STR}/portal/banners", tags=["portal-banners"])
app.include_router(language_admin_router, prefix=f"{settings.API_V1_STR}/admin/languages", tags=["admin-languages"])
app.include_router(language_portal_router, prefix=f"{settings.API_V1_STR}/portal/languages", tags=["portal-languages"])
app.include_router(translation_router, prefix=f"{settings.API_V1_STR}/translation", tags=["translation"])
app.include_router(ai_hub_router, prefix=f"{settings.API_V1_STR}/ai-hub", tags=["ai-hub"])
app.include_router(search_router, prefix=f"{settings.API_V1_STR}/admin/search", tags=["admin-search"])

