"""seed postgraduate information technology programme

Revision ID: d2f9a61b4c8e
Revises: c7b4e2910a63
"""

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import NullType, TypeEngine

revision: str = "d2f9a61b4c8e"
down_revision: str | None = "c7b4e2910a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "postgraduate_programs.json"
SEED_NAMESPACE = uuid.UUID("4d260b26-ed02-418a-a19d-7d8d9671f778")
UUID_TYPE = postgresql.UUID(as_uuid=True)


def table(name: str, *columns: str) -> sa.TableClause:
    typed = []
    for column in columns:
        column_type: TypeEngine = UUID_TYPE if column.endswith("_id") else NullType()
        if column == "id":
            column_type = UUID_TYPE
        typed.append(sa.column(column, column_type))
    return sa.table(name, *typed)


languages = table("languages", "id", "code")
departments = table("departments", "id", "code")
programs = table(
    "programs",
    "id",
    "created_at",
    "updated_at",
    "department_id",
    "code",
    "degree_level",
    "duration_years",
    "training_mode",
    "thumbnail_object_key",
    "sort_order",
    "is_active",
    "is_published",
    "deleted_at",
)
program_translations = table(
    "program_translations",
    "id",
    "created_at",
    "updated_at",
    "program_id",
    "language_id",
    "name",
    "slug",
    "short_description",
    "description",
    "career_opportunities",
    "admissions_info",
)
program_versions = table(
    "program_versions",
    "id",
    "created_at",
    "updated_at",
    "program_id",
    "version_year",
    "cohort_code",
    "total_credits",
    "is_current",
    "is_published",
    "sort_order",
)
program_version_translations = table(
    "program_version_translations",
    "id",
    "created_at",
    "updated_at",
    "version_id",
    "language_id",
    "title",
    "summary",
    "general_objective",
    "career_opportunities",
)
program_documents = table(
    "program_documents",
    "id",
    "created_at",
    "updated_at",
    "version_id",
    "document_type",
    "source_url",
    "object_key",
    "mime_type",
    "file_size",
    "page_count",
    "checksum_sha256",
    "sort_order",
)
program_document_translations = table(
    "program_document_translations",
    "id",
    "created_at",
    "updated_at",
    "document_id",
    "language_id",
    "title",
    "description",
)
program_courses = table(
    "program_courses",
    "id",
    "created_at",
    "updated_at",
    "version_id",
    "course_code",
    "row_type",
    "credits",
    "credits_text",
    "semester",
    "knowledge_block",
    "course_type",
    "managing_unit",
    "sort_order",
)
program_course_translations = table(
    "program_course_translations",
    "id",
    "created_at",
    "updated_at",
    "course_id",
    "language_id",
    "name",
)
menus = table("menus", "id", "code")
menu_items = table(
    "menu_items",
    "id",
    "created_at",
    "updated_at",
    "menu_id",
    "parent_id",
    "target_type",
    "target_id",
    "open_in_new_tab",
    "depth",
    "sort_order",
    "is_visible",
)
menu_item_translations = table(
    "menu_item_translations",
    "id",
    "created_at",
    "updated_at",
    "menu_item_id",
    "language_id",
    "title",
    "external_url",
)
category_translations = table(
    "category_translations", "category_id", "language_id", "slug"
)


def seed_id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, ":".join(str(part) for part in parts))


def timestamped(row: dict, now: datetime) -> dict:
    return {"created_at": now, "updated_at": now, **row}


def load_seed() -> dict:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise RuntimeError("Unsupported postgraduate programme seed version")
    return payload


def get_languages(bind: sa.Connection) -> dict[str, uuid.UUID]:
    result = dict(
        bind.execute(
            sa.select(languages.c.code, languages.c.id).where(
                languages.c.code.in_(("vi", "en"))
            )
        ).all()
    )
    missing = {"vi", "en"} - result.keys()
    if missing:
        raise RuntimeError(f"Missing required languages: {sorted(missing)}")
    return result


def get_department(bind: sa.Connection, code: str) -> uuid.UUID:
    result = bind.scalar(sa.select(departments.c.id).where(departments.c.code == code))
    if result is None:
        raise RuntimeError(f"Missing required department: {code}")
    return result


def upsert_translation(
    bind: sa.Connection,
    translation_table: sa.TableClause,
    parent_column: sa.ColumnClause,
    parent_id: uuid.UUID,
    parent_kind: str,
    translations: dict,
    language_map: dict[str, uuid.UUID],
    now: datetime,
) -> None:
    for language_code, values in translations.items():
        language_id = language_map.get(language_code)
        if language_id is None:
            continue
        existing_id = bind.scalar(
            sa.select(translation_table.c.id).where(
                parent_column == parent_id,
                translation_table.c.language_id == language_id,
            )
        )
        if existing_id is None:
            bind.execute(
                translation_table.insert().values(
                    **timestamped(
                        {
                            "id": seed_id(
                                parent_kind, parent_id, "translation", language_code
                            ),
                            parent_column.name: parent_id,
                            "language_id": language_id,
                            **values,
                        },
                        now,
                    )
                )
            )
        else:
            bind.execute(
                translation_table.update()
                .where(translation_table.c.id == existing_id)
                .values(updated_at=now, **values)
            )


def upsert_profile(
    bind: sa.Connection,
    program: dict,
    program_id: uuid.UUID,
    language_map: dict[str, uuid.UUID],
    now: datetime,
) -> None:
    code = program["code"]
    for version in program["profile"]["versions"]:
        year = version["version_year"]
        version_id = bind.scalar(
            sa.select(program_versions.c.id).where(
                program_versions.c.program_id == program_id,
                program_versions.c.version_year == year,
            )
        )
        version_values = {
            "cohort_code": version.get("cohort_code"),
            "total_credits": version.get("total_credits"),
            "is_current": version["is_current"],
            "is_published": version["is_published"],
            "sort_order": version["sort_order"],
        }
        if version_id is None:
            version_id = seed_id("program", code, "version", year)
            bind.execute(
                program_versions.insert().values(
                    **timestamped(
                        {
                            "id": version_id,
                            "program_id": program_id,
                            "version_year": year,
                            **version_values,
                        },
                        now,
                    )
                )
            )
        else:
            bind.execute(
                program_versions.update()
                .where(program_versions.c.id == version_id)
                .values(updated_at=now, **version_values)
            )

        upsert_translation(
            bind,
            program_version_translations,
            program_version_translations.c.version_id,
            version_id,
            "version",
            version["translations"],
            language_map,
            now,
        )

        for index, document in enumerate(version["documents"]):
            document_id = seed_id("program", code, "version", year, "document", index)
            exists = bind.scalar(
                sa.select(program_documents.c.id).where(
                    program_documents.c.id == document_id
                )
            )
            base = {
                key: value for key, value in document.items() if key != "translations"
            }
            if exists is None:
                bind.execute(
                    program_documents.insert().values(
                        **timestamped(
                            {"id": document_id, "version_id": version_id, **base}, now
                        )
                    )
                )
            else:
                bind.execute(
                    program_documents.update()
                    .where(program_documents.c.id == document_id)
                    .values(updated_at=now, **base)
                )
            upsert_translation(
                bind,
                program_document_translations,
                program_document_translations.c.document_id,
                document_id,
                "document",
                document["translations"],
                language_map,
                now,
            )

        for index, course in enumerate(version["courses"]):
            course_id = seed_id("program", code, "version", year, "course", index)
            exists = bind.scalar(
                sa.select(program_courses.c.id).where(program_courses.c.id == course_id)
            )
            base = {
                key: value for key, value in course.items() if key != "translations"
            }
            if exists is None:
                bind.execute(
                    program_courses.insert().values(
                        **timestamped(
                            {"id": course_id, "version_id": version_id, **base}, now
                        )
                    )
                )
            else:
                bind.execute(
                    program_courses.update()
                    .where(program_courses.c.id == course_id)
                    .values(updated_at=now, **base)
                )
            upsert_translation(
                bind,
                program_course_translations,
                program_course_translations.c.course_id,
                course_id,
                "course",
                course["translations"],
                language_map,
                now,
            )


def upsert_programs(bind: sa.Connection, payload: dict, now: datetime) -> None:
    language_map = get_languages(bind)
    for program in payload["programs"]:
        code = program["code"]
        program_id = bind.scalar(
            sa.select(programs.c.id).where(programs.c.code == code)
        )
        base = {
            "department_id": get_department(bind, program["department_code"]),
            "code": code,
            "degree_level": program["degree_level"],
            "duration_years": program["duration_years"],
            "training_mode": program["training_mode"],
            "thumbnail_object_key": None,
            "sort_order": program["sort_order"],
            "is_active": program["is_active"],
            "is_published": program["is_published"],
            "deleted_at": None,
        }
        if program_id is None:
            program_id = seed_id("program", code)
            bind.execute(
                programs.insert().values(**timestamped({"id": program_id, **base}, now))
            )
        else:
            bind.execute(
                programs.update()
                .where(programs.c.id == program_id)
                .values(updated_at=now, **base)
            )
        upsert_translation(
            bind,
            program_translations,
            program_translations.c.program_id,
            program_id,
            "program",
            program["translations"],
            language_map,
            now,
        )
        upsert_profile(bind, program, program_id, language_map, now)


def upsert_menu_translation(
    bind: sa.Connection,
    item_id: uuid.UUID,
    item_kind: str,
    language_code: str,
    language_id: uuid.UUID,
    title: str,
    url: str,
    now: datetime,
) -> None:
    existing_id = bind.scalar(
        sa.select(menu_item_translations.c.id).where(
            menu_item_translations.c.menu_item_id == item_id,
            menu_item_translations.c.language_id == language_id,
        )
    )
    values = {"title": title, "external_url": url}
    if existing_id is None:
        bind.execute(
            menu_item_translations.insert().values(
                **timestamped(
                    {
                        "id": seed_id(item_kind, "translation", language_code),
                        "menu_item_id": item_id,
                        "language_id": language_id,
                        **values,
                    },
                    now,
                )
            )
        )
    else:
        bind.execute(
            menu_item_translations.update()
            .where(menu_item_translations.c.id == existing_id)
            .values(updated_at=now, **values)
        )


def upsert_menu_item(
    bind: sa.Connection,
    menu_id: uuid.UUID,
    parent_id: uuid.UUID,
    existing_id: uuid.UUID | None,
    kind: str,
    depth: int,
    sort_order: int,
    translations: dict[str, tuple[str, str]],
    language_map: dict[str, uuid.UUID],
    now: datetime,
) -> uuid.UUID:
    item_id = existing_id or seed_id(kind)
    values = {
        "menu_id": menu_id,
        "parent_id": parent_id,
        "target_type": "EXTERNAL_LINK",
        "target_id": None,
        "open_in_new_tab": False,
        "depth": depth,
        "sort_order": sort_order,
        "is_visible": True,
    }
    if existing_id is None:
        bind.execute(
            menu_items.insert().values(**timestamped({"id": item_id, **values}, now))
        )
    else:
        bind.execute(
            menu_items.update()
            .where(menu_items.c.id == item_id)
            .values(updated_at=now, **values)
        )
    for language_code, (title, url) in translations.items():
        upsert_menu_translation(
            bind,
            item_id,
            kind,
            language_code,
            language_map[language_code],
            title,
            url,
            now,
        )
    return item_id


def upsert_menu(bind: sa.Connection, now: datetime) -> None:
    language_map = get_languages(bind)
    menu_id = bind.scalar(sa.select(menus.c.id).where(menus.c.code == "header"))
    if menu_id is None:
        return
    training_id = bind.scalar(
        sa.select(menu_items.c.id).where(
            menu_items.c.menu_id == menu_id,
            menu_items.c.parent_id.is_(None),
            menu_items.c.depth == 1,
            menu_items.c.sort_order == 200,
        )
    )
    if training_id is None:
        return
    parent_id = bind.scalar(
        sa.select(menu_items.c.id).where(
            menu_items.c.menu_id == menu_id,
            menu_items.c.parent_id == training_id,
            menu_items.c.depth == 2,
            menu_items.c.sort_order == 220,
        )
    )
    parent_id = upsert_menu_item(
        bind,
        menu_id,
        training_id,
        parent_id,
        "postgraduate-menu",
        2,
        220,
        {
            "vi": ("Đào tạo sau đại học", "/dao-tao/sau-dai-hoc"),
            "en": ("Postgraduate education", "/academics/postgraduate"),
        },
        language_map,
        now,
    )
    child_id = bind.scalar(
        sa.select(menu_items.c.id).where(
            menu_items.c.menu_id == menu_id,
            menu_items.c.parent_id == parent_id,
            menu_items.c.depth == 3,
            menu_items.c.sort_order == 230,
        )
    )
    upsert_menu_item(
        bind,
        menu_id,
        parent_id,
        child_id,
        "postgraduate-it-menu",
        3,
        230,
        {
            "vi": (
                "Thạc sĩ Công nghệ thông tin",
                "/dao-tao/sau-dai-hoc/thac-si-cong-nghe-thong-tin",
            ),
            "en": (
                "Master of Information Technology",
                "/academics/postgraduate/master-of-information-technology",
            ),
        },
        language_map,
        now,
    )


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)
    upsert_programs(bind, load_seed(), now)
    upsert_menu(bind, now)


def restore_category_target(
    bind: sa.Connection, item_id: uuid.UUID | None, slug: str
) -> None:
    if item_id is None:
        return
    language_id = bind.scalar(sa.select(languages.c.id).where(languages.c.code == "vi"))
    category_id = bind.scalar(
        sa.select(category_translations.c.category_id).where(
            category_translations.c.language_id == language_id,
            category_translations.c.slug == slug,
        )
    )
    bind.execute(
        menu_items.update()
        .where(menu_items.c.id == item_id)
        .values(target_type="CATEGORY", target_id=category_id)
    )
    bind.execute(
        menu_item_translations.update()
        .where(menu_item_translations.c.menu_item_id == item_id)
        .values(external_url=None)
    )


def downgrade() -> None:
    bind = op.get_bind()
    program_id = seed_id("program", "60.48.02.01")
    bind.execute(programs.delete().where(programs.c.id == program_id))

    created_child_id = seed_id("postgraduate-it-menu")
    created_parent_id = seed_id("postgraduate-menu")
    bind.execute(menu_items.delete().where(menu_items.c.id == created_child_id))
    bind.execute(menu_items.delete().where(menu_items.c.id == created_parent_id))

    menu_id = bind.scalar(sa.select(menus.c.id).where(menus.c.code == "header"))
    if menu_id is None:
        return
    parent_id = bind.scalar(
        sa.select(menu_items.c.id).where(
            menu_items.c.menu_id == menu_id,
            menu_items.c.depth == 2,
            menu_items.c.sort_order == 220,
        )
    )
    child_id = bind.scalar(
        sa.select(menu_items.c.id).where(
            menu_items.c.menu_id == menu_id,
            menu_items.c.parent_id == parent_id,
            menu_items.c.depth == 3,
            menu_items.c.sort_order == 230,
        )
    )
    restore_category_target(bind, parent_id, "dao-tao-sau-dai-hoc")
    restore_category_target(bind, child_id, "nganh-thac-sy-cong-nghe-thong-tin")
