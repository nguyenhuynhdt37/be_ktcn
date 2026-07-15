"""Export the approved undergraduate programme data for Alembic seeding."""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.main  # noqa: F401
from app.core.database import SessionLocal
from app.modules.program.models import (
    Program,
    ProgramCourse,
    ProgramDocument,
    ProgramOutcome,
    ProgramVersion,
)
from app.modules.program.routers import academic_profile_response

PROGRAM_CODES = (
    "7520207",
    "7520216",
    "52510301",
    "7480201",
    "7480201-CLC",
    "7510205",
    "7510206",
    "7520210",
)
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "data"
    / "undergraduate_programs.json"
)


async def export_seed() -> None:
    async with SessionLocal() as db:
        items = list(
            (
                await db.execute(
                    select(Program)
                    .where(Program.code.in_(PROGRAM_CODES))
                    .options(
                        selectinload(Program.translations),
                        selectinload(Program.versions).selectinload(
                            ProgramVersion.translations
                        ),
                        selectinload(Program.versions)
                        .selectinload(ProgramVersion.documents)
                        .selectinload(ProgramDocument.translations),
                        selectinload(Program.versions)
                        .selectinload(ProgramVersion.outcomes)
                        .selectinload(ProgramOutcome.translations),
                        selectinload(Program.versions)
                        .selectinload(ProgramVersion.courses)
                        .selectinload(ProgramCourse.translations),
                    )
                    .order_by(Program.sort_order)
                )
            )
            .scalars()
            .unique()
        )

        found_codes = {item.code for item in items}
        missing = set(PROGRAM_CODES) - found_codes
        if missing:
            raise RuntimeError(f"Missing undergraduate programmes: {sorted(missing)}")

        programs = []
        for item in items:
            translations = {
                translation.language.code: {
                    "name": translation.name,
                    "slug": translation.slug,
                    "short_description": translation.short_description,
                    "description": translation.description,
                    "career_opportunities": translation.career_opportunities,
                    "admissions_info": translation.admissions_info,
                }
                for translation in item.translations
                if translation.language.code in {"vi", "en"}
            }
            programs.append(
                {
                    "department_code": "FESD",
                    "code": item.code,
                    "degree_level": item.degree_level,
                    "duration_years": (
                        float(item.duration_years)
                        if item.duration_years is not None
                        else None
                    ),
                    "training_mode": item.training_mode,
                    "sort_order": item.sort_order,
                    "is_active": item.is_active,
                    "is_published": item.is_published,
                    "translations": translations,
                    "profile": academic_profile_response(item).model_dump(mode="json"),
                }
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {"schema_version": 1, "programs": programs},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Exported {len(programs)} programmes to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(export_seed())
