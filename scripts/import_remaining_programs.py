"""Import the remaining crawled undergraduate programme profiles."""

import asyncio
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select

import app.main  # noqa: F401
from app.core.database import SessionLocal
from app.modules.department.models import Department
from app.modules.language.models import Language
from app.modules.program.models import Program, ProgramTranslation
from app.modules.program.schemas import ProgramAcademicProfileInput
from app.modules.program.service import program_service

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "scratch" / "legacy_programs_raw"
PDF_DATA_PATH = Path(__file__).resolve().parent / "data" / "program_pdf_extracted.json"


@dataclass(frozen=True)
class ProgramDefinition:
    source_dir: str
    code: str
    name_vi: str
    name_en: str
    slug_vi: str
    slug_en: str
    duration_years: float
    short_vi: str
    short_en: str
    sort_order: int
    build_profile: Callable[[], ProgramAcademicProfileInput]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().replace(" ,", ",")


def clean_code(value: str) -> str:
    return clean_text(value).replace(" ", "").rstrip(".")


def load_source(source_dir: str) -> tuple[list[dict], list[dict], str]:
    directory = SOURCE_ROOT / source_dir
    elements = json.loads((directory / "content_elements.json").read_text("utf-8"))
    assets = json.loads((directory / "assets.json").read_text("utf-8"))
    content = (directory / "content.txt").read_text("utf-8")
    return elements["tables"], assets, content


def load_pdf_program_data(program_code: str) -> dict:
    payload = json.loads(PDF_DATA_PATH.read_text("utf-8"))
    return payload[program_code]


def section(text: str, start: str, end: str) -> str:
    normalized = clean_text(text)
    return clean_text(normalized.split(start, 1)[1].split(end, 1)[0])


def line_after(text: str, marker: str) -> str:
    lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]
    return lines[lines.index(marker) + 1]


def translated_content(content: str) -> dict:
    return {"vi": {"content": clean_text(content)}}


def outcome(
    code: str,
    content: str,
    outcome_type: str,
    sort_order: int,
    parent_code: str | None = None,
) -> dict:
    return {
        "code": clean_code(code),
        "outcome_type": outcome_type,
        "parent_code": clean_code(parent_code) if parent_code else None,
        "sort_order": sort_order,
        "translations": translated_content(content),
    }


def credits_value(value: str | None) -> float | None:
    if not value:
        return None
    normalized = clean_text(value).replace(",", ".")
    return float(normalized) if re.fullmatch(r"\d+(?:\.\d+)?", normalized) else None


def course(
    name: str,
    sort_order: int,
    *,
    course_code: str | None = None,
    row_type: str = "course",
    credits_text: str | None = None,
    semester: str | None = None,
    knowledge_block: str | None = None,
    course_type: str | None = None,
    managing_unit: str | None = None,
) -> dict:
    normalized_credits = clean_text(credits_text) if credits_text else None
    return {
        "course_code": clean_text(course_code) if course_code else None,
        "row_type": row_type,
        "credits": credits_value(normalized_credits),
        "credits_text": normalized_credits,
        "semester": clean_text(semester) if semester else None,
        "knowledge_block": clean_text(knowledge_block) if knowledge_block else None,
        "course_type": clean_text(course_type) if course_type else None,
        "managing_unit": clean_text(managing_unit) if managing_unit else None,
        "sort_order": sort_order,
        "translations": {"vi": {"name": clean_text(name)}},
    }


def group_course(name: str, sort_order: int) -> dict:
    return course(name, sort_order, row_type="group")


def pdf_courses(program_code: str) -> list[dict]:
    rows = load_pdf_program_data(program_code)["courses"]
    return [
        course(
            row["name"],
            sort_order,
            course_code=row["course_code"],
            row_type=row["row_type"],
            credits_text=row["credits_text"],
            semester=row["semester"],
            knowledge_block=row["knowledge_block"],
        )
        for sort_order, row in enumerate(rows)
    ]


def document(
    asset: dict,
    document_type: str,
    title_vi: str,
    title_en: str,
    page_count: int,
    sort_order: int = 0,
) -> dict:
    return {
        "document_type": document_type,
        "source_url": asset["final_url"],
        "mime_type": "application/pdf",
        "file_size": asset["size_bytes"],
        "page_count": page_count,
        "checksum_sha256": asset["sha256"],
        "sort_order": sort_order,
        "translations": {
            "vi": {"title": title_vi},
            "en": {"title": title_en},
        },
    }


def version(
    year: int,
    title_vi: str,
    title_en: str,
    *,
    cohort_code: str | None = None,
    total_credits: float | None = None,
    is_current: bool = True,
    sort_order: int = 0,
    general_objective: str | None = None,
    career_opportunities: str | None = None,
    documents: list[dict] | None = None,
    outcomes: list[dict] | None = None,
    courses: list[dict] | None = None,
) -> dict:
    return {
        "version_year": year,
        "cohort_code": cohort_code,
        "total_credits": total_credits,
        "is_current": is_current,
        "is_published": True,
        "sort_order": sort_order,
        "translations": {
            "vi": {
                "title": title_vi,
                "summary": (
                    "Hồ sơ chương trình đào tạo được số hóa từ nguồn "
                    "công bố của đơn vị."
                ),
                "general_objective": general_objective,
                "career_opportunities": career_opportunities,
            },
            "en": {
                "title": title_en,
                "summary": (
                    "Digitised programme record from the unit's published source."
                ),
            },
        },
        "documents": documents or [],
        "outcomes": outcomes or [],
        "courses": courses or [],
    }


def build_automation_profile() -> ProgramAcademicProfileInput:
    tables, assets, content = load_source("02_automation_control")
    pdf_data = load_pdf_program_data("7520216")
    general_objective = line_after(content, "1. Mục tiêu")

    def parse_outcomes(table_index: int) -> list[dict]:
        parsed = []
        for index, row in enumerate(tables[table_index]["rows"][1:]):
            code = clean_code(row[0])
            if code and clean_text(row[1]):
                parent = ".".join(code.split(".")[:-1]) if "." in code else None
                parsed.append(outcome(code, row[1], "learning_outcome", index, parent))
        return parsed

    versions = [
        version(
            2019,
            "Chương trình đào tạo 2019 - K60",
            "2019 Curriculum - K60",
            cohort_code="K60",
            total_credits=pdf_data["total_credits"],
            general_objective=general_objective,
            documents=[
                document(
                    assets[0],
                    "specification",
                    "Bản mô tả chương trình đào tạo K60",
                    "K60 Programme Specification",
                    38,
                )
            ],
            outcomes=parse_outcomes(0),
            courses=pdf_courses("7520216"),
        ),
        version(
            2017,
            "Chương trình đào tạo 2017 - K58",
            "2017 Curriculum - K58",
            cohort_code="K58",
            is_current=False,
            sort_order=1,
            documents=[
                document(
                    assets[1],
                    "specification",
                    "Bản mô tả chương trình đào tạo K58",
                    "K58 Programme Specification",
                    31,
                )
            ],
            outcomes=parse_outcomes(2),
        ),
        version(
            2015,
            "Chương trình đào tạo 2015 - K56",
            "2015 Curriculum - K56",
            cohort_code="K56",
            is_current=False,
            sort_order=2,
            documents=[
                document(
                    assets[2],
                    "curriculum",
                    "Chương trình đào tạo K56",
                    "K56 Curriculum",
                    37,
                )
            ],
        ),
    ]
    return ProgramAcademicProfileInput(versions=versions)


def build_electrical_profile() -> ProgramAcademicProfileInput:
    tables, _, _ = load_source("03_electrical_electronics")
    objective_table = tables[0]["rows"]
    general_objective = clean_text(objective_table[0][0]).split(":", 1)[1].strip()
    outcomes = []
    for index, row in enumerate(objective_table[2:]):
        major = clean_code(row[0])
        minor = clean_code(row[1])
        if row[1] == row[2]:
            outcomes.append(outcome(f"PO{major}", row[1], "objective", index))
        else:
            outcomes.append(
                outcome(
                    f"PLO{major}.{minor}",
                    row[2],
                    "learning_outcome",
                    index,
                    f"PO{major}",
                )
            )

    block_names = (
        "Kiến thức giáo dục đại cương",
        "Kiến thức khoa học cơ bản",
        "Kiến thức cơ sở ngành",
        "Kiến thức ngành bắt buộc",
        "Tự chọn định hướng Hệ thống điện",
        "Tự chọn định hướng Thiết bị điện",
    )
    courses = []
    for table_index, block_name in enumerate(block_names, start=1):
        courses.append(group_course(block_name, len(courses)))
        for row in tables[table_index]["rows"][1:]:
            courses.append(
                course(
                    row[1],
                    len(courses),
                    credits_text=row[3],
                    knowledge_block=block_name,
                    course_type=row[2],
                )
            )

    profile_version = version(
        2017,
        "Chương trình đào tạo 2017",
        "2017 Curriculum",
        general_objective=general_objective,
        outcomes=outcomes,
        courses=courses,
    )
    return ProgramAcademicProfileInput(versions=[profile_version])


def build_information_technology_profile() -> ProgramAcademicProfileInput:
    tables, assets, content = load_source("04_information_technology")
    pdf_data = load_pdf_program_data("7480201")
    general_objective = line_after(content, "2.1. Mục tiêu tổng quát")
    outcomes = [
        outcome(f"PO{row[0]}", row[1], "objective", index)
        for index, row in enumerate(tables[1]["rows"])
    ]
    for index, row in enumerate(tables[2]["rows"]):
        code = clean_code(row[0])
        if "." not in code:
            continue
        outcomes.append(
            outcome(
                f"PLO{code}",
                row[1],
                "learning_outcome",
                index,
                f"PO{code.split('.', 1)[0]}",
            )
        )

    profile_version = version(
        2017,
        "Chương trình đào tạo 2017",
        "2017 Curriculum",
        total_credits=pdf_data["total_credits"],
        general_objective=general_objective,
        career_opportunities=pdf_data["career_opportunities"],
        documents=[
            document(
                assets[0],
                "specification",
                "Bản đặc tả chương trình đào tạo năm 2017",
                "2017 Programme Specification",
                75,
            )
        ],
        outcomes=outcomes,
        courses=pdf_courses("7480201"),
    )
    return ProgramAcademicProfileInput(versions=[profile_version])


def build_high_quality_it_profile() -> ProgramAcademicProfileInput:
    tables, _, _ = load_source("05_information_technology_high_quality")
    courses = [group_course("Kế hoạch giảng dạy", 0)]
    for row in tables[7]["rows"][1:]:
        name = clean_text(row[1])
        is_summary = "tổng số tín chỉ" in name.lower()
        courses.append(
            course(
                name,
                len(courses),
                row_type="summary" if is_summary else "course",
                credits_text=row[3],
                semester=row[5],
                course_type=row[2],
            )
        )
    for table_index, block_name in (
        (8, "Tự chọn chuyên ngành Khoa học máy tính"),
        (9, "Tự chọn chuyên ngành Công nghệ phần mềm"),
    ):
        courses.append(group_course(block_name, len(courses)))
        for row in tables[table_index]["rows"][1:]:
            courses.append(
                course(
                    row[1],
                    len(courses),
                    credits_text=row[3],
                    semester=row[5],
                    knowledge_block=block_name,
                    course_type=row[2],
                )
            )

    profile_version = version(
        2018,
        "Chương trình chất lượng cao 2018",
        "2018 High-Quality Curriculum",
        total_credits=150,
        courses=courses,
    )
    return ProgramAcademicProfileInput(versions=[profile_version])


def build_automotive_profile() -> ProgramAcademicProfileInput:
    tables, _, _ = load_source("06_automotive_engineering_technology")
    general_objective = clean_text(tables[1]["rows"][-1][0])
    courses = []
    for table_index, block_name in (
        (2, "Kiến thức giáo dục đại cương"),
        (3, "Kiến thức cơ sở ngành"),
        (4, "Kiến thức ngành"),
        (5, "Đồ án và tốt nghiệp"),
    ):
        courses.append(group_course(block_name, len(courses)))
        for row in tables[table_index]["rows"][1:]:
            name = clean_text(row[1])
            is_summary = name.lower() == "tổng"
            row_type = "summary" if is_summary else "course"
            if not clean_text(row[0]) and not clean_text(row[2]):
                row_type = "placeholder"
            courses.append(
                course(
                    name,
                    len(courses),
                    row_type=row_type,
                    credits_text=row[2],
                    knowledge_block=block_name,
                )
            )
    for table_index in range(6, 10):
        rows = tables[table_index]["rows"]
        block_name = clean_text(rows[0][0])
        courses.append(group_course(block_name, len(courses)))
        for row in rows[2:]:
            courses.append(
                course(
                    row[2],
                    len(courses),
                    course_code=row[1],
                    credits_text=row[3],
                    knowledge_block=block_name,
                    course_type="Tự chọn",
                )
            )

    profile_version = version(
        2020,
        "Chương trình đào tạo 2020",
        "2020 Curriculum",
        total_credits=150,
        general_objective=general_objective,
        courses=courses,
    )
    return ProgramAcademicProfileInput(versions=[profile_version])


def build_thermal_profile() -> ProgramAcademicProfileInput:
    tables, _, _ = load_source("07_thermal_engineering_technology")
    general_objective = clean_text(tables[1]["rows"][0][0]).split(":", 1)[1]
    outcomes = [
        outcome(row[0], row[1], "objective", index)
        for index, row in enumerate(tables[1]["rows"][2:])
    ]
    for index, row in enumerate(tables[4]["rows"][1:]):
        code = clean_code(row[0])
        if code.startswith("PLO"):
            parent = f"PO{code[3:].split('.', 1)[0]}"
        else:
            parts = code.split(".")
            parent = f"PLO{parts[0]}.{parts[1]}" if len(parts) > 2 else None
        outcomes.append(outcome(code, row[1], "learning_outcome", index, parent))

    profile_version = version(
        2017,
        "Mục tiêu và chuẩn đầu ra chương trình 2017",
        "2017 Programme Objectives and Learning Outcomes",
        total_credits=150,
        general_objective=general_objective,
        outcomes=outcomes,
    )
    return ProgramAcademicProfileInput(versions=[profile_version])


def build_electronics_informatics_profile() -> ProgramAcademicProfileInput:
    tables, _, content = load_source("08_electronics_informatics")
    general_objective = section(content, "1.1. Mục tiêu chung", "1.2. Mục tiêu cụ thể")
    outcomes = [
        outcome(f"PO{row[0]}", row[1], "objective", index)
        for index, row in enumerate(tables[1]["rows"])
    ]
    for index, row in enumerate(tables[2]["rows"]):
        code = clean_code(row[0])
        if "." not in code:
            continue
        outcomes.append(
            outcome(
                f"PLO{code}",
                row[1],
                "learning_outcome",
                index,
                f"PO{code.split('.', 1)[0]}",
            )
        )

    courses = []
    seen_course_codes: set[str] = set()
    for row in tables[14]["rows"][1:]:
        if len(set(row)) == 1:
            courses.append(group_course(row[0], len(courses)))
            continue
        if clean_text(row[1]).lower().startswith("tổng") and not clean_text(row[2]):
            courses.append(
                course(
                    row[1],
                    len(courses),
                    row_type="summary",
                    credits_text=row[3],
                )
            )
            continue
        source_code = clean_text(row[1]) or None
        stored_code = source_code if source_code not in seen_course_codes else None
        if source_code:
            seen_course_codes.add(source_code)
        courses.append(
            course(
                row[2],
                len(courses),
                course_code=stored_code,
                credits_text=row[3],
                semester=row[10],
                knowledge_block=row[11],
                course_type=row[12],
                managing_unit=row[13],
            )
        )

    profile_version = version(
        2021,
        "Chương trình đào tạo 2021",
        "2021 Curriculum",
        total_credits=150,
        general_objective=general_objective,
        outcomes=outcomes,
        courses=courses,
    )
    return ProgramAcademicProfileInput(versions=[profile_version])


PROGRAMS = (
    ProgramDefinition(
        "02_automation_control",
        "7520216",
        "Kỹ thuật Điều khiển và Tự động hóa",
        "Control and Automation Engineering",
        "ky-thuat-dieu-khien-va-tu-dong-hoa",
        "control-and-automation-engineering",
        5.0,
        "Chương trình kỹ sư về đo lường, điều khiển và tự động hóa.",
        "Engineering programme in measurement, control and automation.",
        1,
        build_automation_profile,
    ),
    ProgramDefinition(
        "03_electrical_electronics",
        "52510301",
        "Công nghệ kỹ thuật Điện - Điện tử",
        "Electrical and Electronic Engineering Technology",
        "cong-nghe-ky-thuat-dien-dien-tu",
        "electrical-and-electronic-engineering-technology",
        5.0,
        "Chương trình công nghệ kỹ thuật điện, điện tử hệ chính quy.",
        "Full-time electrical and electronic engineering technology programme.",
        2,
        build_electrical_profile,
    ),
    ProgramDefinition(
        "04_information_technology",
        "7480201",
        "Công nghệ thông tin",
        "Information Technology",
        "cong-nghe-thong-tin",
        "information-technology",
        5.0,
        "Chương trình đào tạo đại học ngành Công nghệ thông tin.",
        "Undergraduate programme in Information Technology.",
        3,
        build_information_technology_profile,
    ),
    ProgramDefinition(
        "05_information_technology_high_quality",
        "7480201-CLC",
        "Công nghệ thông tin chất lượng cao",
        "High-Quality Information Technology",
        "cong-nghe-thong-tin-chat-luong-cao",
        "high-quality-information-technology",
        4.5,
        "Chương trình Công nghệ thông tin chất lượng cao, khối lượng 150 tín chỉ.",
        "A 150-credit high-quality Information Technology programme.",
        4,
        build_high_quality_it_profile,
    ),
    ProgramDefinition(
        "06_automotive_engineering_technology",
        "7510205",
        "Công nghệ kỹ thuật Ô tô",
        "Automotive Engineering Technology",
        "cong-nghe-ky-thuat-o-to",
        "automotive-engineering-technology",
        4.5,
        "Chương trình kỹ sư Công nghệ kỹ thuật Ô tô, khối lượng 150 tín chỉ.",
        "A 150-credit Automotive Engineering Technology programme.",
        5,
        build_automotive_profile,
    ),
    ProgramDefinition(
        "07_thermal_engineering_technology",
        "7510206",
        "Công nghệ kỹ thuật Nhiệt",
        "Thermal Engineering Technology",
        "cong-nghe-ky-thuat-nhiet",
        "thermal-engineering-technology",
        4.5,
        "Chương trình kỹ sư chuyên ngành Nhiệt - Điện lạnh.",
        "Engineering programme specialising in thermal and refrigeration systems.",
        6,
        build_thermal_profile,
    ),
    ProgramDefinition(
        "08_electronics_informatics",
        "7520210",
        "Kỹ thuật Điện tử và Tin học",
        "Electronic Engineering and Informatics",
        "ky-thuat-dien-tu-va-tin-hoc",
        "electronic-engineering-and-informatics",
        4.5,
        (
            "Chương trình kỹ sư kết hợp điện tử, hệ thống nhúng IoT "
            "và công nghệ thông tin."
        ),
        "Engineering programme combining electronics, embedded IoT and IT.",
        7,
        build_electronics_informatics_profile,
    ),
)


async def import_programs() -> None:
    async with SessionLocal() as db:
        department = (
            await db.execute(select(Department).where(Department.code == "FESD"))
        ).scalar_one()
        languages = {
            language.code: language
            for language in (await db.execute(select(Language))).scalars()
        }

        for definition in PROGRAMS:
            profile = definition.build_profile()
            program = (
                await db.execute(select(Program).where(Program.code == definition.code))
            ).scalar_one_or_none()
            if program is None:
                program = Program(
                    department_id=department.id,
                    code=definition.code,
                    degree_level="bachelor",
                    duration_years=definition.duration_years,
                    training_mode="full_time",
                    sort_order=definition.sort_order,
                    is_active=True,
                    is_published=True,
                    translations=[],
                )
                db.add(program)
                await db.flush()
            else:
                program.department_id = department.id
                program.duration_years = definition.duration_years
                program.training_mode = "full_time"
                program.sort_order = definition.sort_order
                program.is_active = True
                program.is_published = True

            existing = {
                translation.language.code: translation
                for translation in program.translations
            }
            translated_values = {
                "vi": {
                    "name": definition.name_vi,
                    "slug": definition.slug_vi,
                    "short_description": definition.short_vi,
                },
                "en": {
                    "name": definition.name_en,
                    "slug": definition.slug_en,
                    "short_description": definition.short_en,
                },
            }
            for code, values in translated_values.items():
                translation = existing.get(code)
                if translation is None:
                    translation = ProgramTranslation(
                        program_id=program.id,
                        language_id=languages[code].id,
                    )
                    db.add(translation)
                    existing[code] = translation
                for field, value in values.items():
                    setattr(translation, field, value)

            await program_service.save_academic_profile(db, program.id, profile)
            current = next(item for item in profile.versions if item.is_current)
            career = current.translations.get("vi")
            if career and career.career_opportunities:
                existing["vi"].career_opportunities = career.career_opportunities
            print(
                f"{definition.code}: {len(profile.versions)} version(s), "
                f"{sum(len(item.documents) for item in profile.versions)} document(s), "
                f"{len(current.outcomes)} outcome(s), "
                f"{len(current.courses)} curriculum row(s)"
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(import_programs())
