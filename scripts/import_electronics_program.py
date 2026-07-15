"""Import the crawled Electronics and Telecommunications programme profile."""

import asyncio
import json
import re
from pathlib import Path

from sqlalchemy import select

import app.main  # noqa: F401
from app.core.database import SessionLocal
from app.modules.department.models import Department
from app.modules.language.models import Language
from app.modules.program.models import Program, ProgramTranslation
from app.modules.program.schemas import ProgramAcademicProfileInput
from app.modules.program.service import program_service

SOURCE_DIR = (
    Path(__file__).resolve().parents[1]
    / "scratch"
    / "legacy_programs_raw"
    / "01_electronics_telecommunications"
)


def clean_text(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    return (
        cleaned.replace("Đ iện", "Điện")
        .replace("chuyên ngànhvào", "chuyên ngành vào")
        .replace("máy tinh", "máy tính")
        .replace(" ,", ",")
    )


def section(text: str, start: str, end: str) -> str:
    normalized = clean_text(text)
    return clean_text(normalized.split(start, 1)[1].split(end, 1)[0])


def document_payload(asset: dict, *, year: int, kind: str, pages: int) -> dict:
    cohort = {2017: "K58", 2019: "K61", 2022: "K62"}[year]
    if kind == "specification":
        title_vi = f"Bản mô tả chương trình đào tạo năm {year}"
        title_en = f"{year} Programme Specification"
    else:
        title_vi = f"Chương trình đào tạo Điện tử - Viễn thông {cohort}"
        title_en = f"Electronics and Telecommunications Curriculum {cohort}"
    return {
        "document_type": kind,
        "source_url": asset["final_url"],
        "mime_type": "application/pdf",
        "file_size": asset["size_bytes"],
        "page_count": pages,
        "checksum_sha256": asset["sha256"],
        "sort_order": 0 if kind == "specification" else 1,
        "translations": {
            "vi": {"title": title_vi},
            "en": {"title": title_en},
        },
    }


def build_profile() -> ProgramAcademicProfileInput:
    elements = json.loads((SOURCE_DIR / "content_elements.json").read_text("utf-8"))
    assets = json.loads((SOURCE_DIR / "assets.json").read_text("utf-8"))
    content = (SOURCE_DIR / "content.txt").read_text("utf-8")

    general_objective = section(content, "Mục tiêu chung (PO)", "Mục tiêu cụ thể")
    career = section(
        content,
        "Định hướng việc làm sau khi tốt nghiệp",
        "Khung chương trình đào tạo",
    )

    objectives = [
        {
            "code": clean_text(row[0]).rstrip("."),
            "outcome_type": "objective",
            "sort_order": index,
            "translations": {"vi": {"content": clean_text(row[1])}},
        }
        for index, row in enumerate(elements["tables"][1]["rows"])
    ]

    learning_outcomes = []
    parent_code = None
    for index, row in enumerate(elements["tables"][2]["rows"]):
        code = clean_text(row[0]).rstrip(".")
        if code.startswith("PO"):
            parent_code = code
            continue
        learning_outcomes.append(
            {
                "code": code,
                "outcome_type": "learning_outcome",
                "parent_code": parent_code,
                "sort_order": index,
                "translations": {"vi": {"content": clean_text(row[1])}},
            }
        )

    courses = []
    for index, row in enumerate(elements["tables"][3]["rows"][1:]):
        is_group = len(set(row)) == 1
        name = clean_text(row[2] if not is_group else row[0])
        course_code = clean_text(row[1]) if not is_group else ""
        if is_group:
            row_type = "group"
        elif name.lower() == "tổng":
            row_type = "summary"
        elif not course_code:
            row_type = "placeholder"
        else:
            row_type = "course"
        credits_text = clean_text(row[3]) if not is_group else None
        credits = (
            float(credits_text) if credits_text and credits_text.isdigit() else None
        )
        courses.append(
            {
                "course_code": course_code or None,
                "row_type": row_type,
                "credits": credits,
                "credits_text": credits_text,
                "semester": clean_text(row[4]) if not is_group else None,
                "knowledge_block": clean_text(row[5]) if not is_group else None,
                "course_type": clean_text(row[6]) if not is_group else None,
                "managing_unit": clean_text(row[7]) if not is_group else None,
                "sort_order": index,
                "translations": {"vi": {"name": name}},
            }
        )

    version_documents = {
        2017: [
            document_payload(assets[0], year=2017, kind="specification", pages=32),
            document_payload(assets[1], year=2017, kind="curriculum", pages=809),
        ],
        2019: [
            document_payload(assets[3], year=2019, kind="specification", pages=32),
            document_payload(assets[4], year=2019, kind="curriculum", pages=779),
        ],
        2022: [
            document_payload(assets[6], year=2022, kind="specification", pages=86),
            document_payload(assets[7], year=2022, kind="curriculum", pages=439),
        ],
    }

    versions = []
    for sort_order, year in enumerate((2022, 2019, 2017)):
        cohort = {2017: "K58", 2019: "K61", 2022: "K62"}[year]
        versions.append(
            {
                "version_year": year,
                "cohort_code": cohort,
                "total_credits": 150 if year == 2022 else None,
                "is_current": year == 2022,
                "is_published": True,
                "sort_order": sort_order,
                "translations": {
                    "vi": {
                        "title": f"Chương trình đào tạo {year} - {cohort}",
                        "summary": (
                            "Chương trình giáo dục đại học hệ chính quy "
                            "theo tiếp cận CDIO."
                            if year == 2022
                            else "Phiên bản chương trình và đề cương được lưu trữ "
                            "theo khóa tuyển sinh."
                        ),
                        "general_objective": general_objective
                        if year == 2022
                        else None,
                        "career_opportunities": career if year == 2022 else None,
                    },
                    "en": {
                        "title": f"{year} Curriculum - {cohort}",
                        "summary": (
                            "Full-time undergraduate programme following "
                            "the CDIO approach."
                            if year == 2022
                            else "Archived curriculum and syllabi for "
                            "the corresponding intake."
                        ),
                    },
                },
                "documents": version_documents[year],
                "outcomes": objectives + learning_outcomes if year == 2022 else [],
                "courses": courses if year == 2022 else [],
            }
        )
    return ProgramAcademicProfileInput(versions=versions)


async def import_program() -> None:
    profile = build_profile()
    async with SessionLocal() as db:
        department = (
            await db.execute(select(Department).where(Department.code == "FESD"))
        ).scalar_one()
        languages = {
            language.code: language
            for language in (await db.execute(select(Language))).scalars()
        }
        program = (
            await db.execute(select(Program).where(Program.code == "7520207"))
        ).scalar_one_or_none()
        if program is None:
            program = Program(
                department_id=department.id,
                code="7520207",
                degree_level="bachelor",
                duration_years=4.5,
                training_mode="full_time",
                sort_order=0,
                is_active=True,
                is_published=True,
                translations=[],
            )
            db.add(program)
            await db.flush()
        else:
            program.department_id = department.id
            program.duration_years = 4.5
            program.training_mode = "full_time"
            program.is_active = True
            program.is_published = True

        existing = {
            translation.language.code: translation
            for translation in program.translations
        }
        translations = {
            "vi": {
                "name": "Kỹ thuật Điện tử - Viễn thông",
                "slug": "ky-thuat-dien-tu-vien-thong",
                "short_description": (
                    "Chương trình kỹ sư hệ chính quy theo tiếp cận CDIO."
                ),
                "career_opportunities": profile.versions[0]
                .translations["vi"]
                .career_opportunities,
            },
            "en": {
                "name": "Electronics and Telecommunications Engineering",
                "slug": "electronics-and-telecommunications-engineering",
                "short_description": (
                    "A full-time engineering programme following the CDIO approach."
                ),
            },
        }
        for code, values in translations.items():
            translation = existing.get(code)
            if translation is None:
                translation = ProgramTranslation(
                    program_id=program.id,
                    language_id=languages[code].id,
                )
                db.add(translation)
            for field, value in values.items():
                setattr(translation, field, value)

        await program_service.save_academic_profile(db, program.id, profile)
        await db.commit()
        print(
            "Imported 3 versions, 6 documents, "
            f"{len(profile.versions[0].outcomes)} outcomes and "
            f"{len(profile.versions[0].courses)} curriculum rows."
        )


if __name__ == "__main__":
    asyncio.run(import_program())
