"""Initialize a fresh database, or migrate an existing deployment."""

import asyncio
import subprocess

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.common.models.base import Base
from app.core.config import settings

# Import every model so SQLAlchemy has the complete metadata for a fresh schema.
from app.modules.academic_title import models as academic_title_models  # noqa: F401
from app.modules.ai_hub import models as ai_hub_models  # noqa: F401
from app.modules.article import models as article_models  # noqa: F401
from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.banner import models as banner_models  # noqa: F401
from app.modules.category import models as category_models  # noqa: F401
from app.modules.consultation import models as consultation_models  # noqa: F401
from app.modules.degree import models as degree_models  # noqa: F401
from app.modules.department import models as department_models  # noqa: F401
from app.modules.gallery import models as gallery_models  # noqa: F401
from app.modules.language import models as language_models  # noqa: F401
from app.modules.media import models as media_models  # noqa: F401
from app.modules.menu import models as menu_models  # noqa: F401
from app.modules.notification import models as notification_models  # noqa: F401
from app.modules.position import models as position_models  # noqa: F401
from app.modules.program import models as program_models  # noqa: F401
from app.modules.staff import models as staff_models  # noqa: F401
from app.modules.statistics import models as statistics_models  # noqa: F401
from app.modules.tag import models as tag_models  # noqa: F401


async def database_is_empty() -> bool:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT NOT EXISTS ("
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                    ")"
                )
            )
            return bool(result.scalar_one())
    finally:
        await engine.dispose()


async def create_schema() -> None:
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


def main() -> None:
    if asyncio.run(database_is_empty()):
        print("Database is empty; creating the current application schema.")
        asyncio.run(create_schema())
        subprocess.run(["alembic", "stamp", "head"], check=True)
        return

    subprocess.run(["alembic", "upgrade", "head"], check=True)


if __name__ == "__main__":
    main()
