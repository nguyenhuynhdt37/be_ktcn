"""seed undergraduate programmes

Revision ID: c7b4e2910a63
Revises: a12f4c8e9d31
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

revision: str = "c7b4e2910a63"
down_revision: str | None = "a12f4c8e9d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "undergraduate_programs.json"
SEED_NAMESPACE = uuid.UUID("569e2146-f30f-48ab-bd79-190ad38bc78b")
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
program_outcomes = table(
    "program_outcomes",
    "id",
    "created_at",
    "updated_at",
    "version_id",
    "code",
    "outcome_type",
    "parent_code",
    "sort_order",
)
program_outcome_translations = table(
    "program_outcome_translations",
    "id",
    "created_at",
    "updated_at",
    "outcome_id",
    "language_id",
    "content",
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


def seed_id(*parts: object) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, ":".join(str(part) for part in parts))


def load_seed() -> dict:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise RuntimeError("Unsupported undergraduate programme seed version")
    return payload


def timestamped(row: dict, now: datetime) -> dict:
    return {"created_at": now, "updated_at": now, **row}


def language_ids(bind: sa.Connection) -> dict[str, uuid.UUID]:
    rows = bind.execute(
        sa.select(languages.c.code, languages.c.id).where(
            languages.c.code.in_(("vi", "en"))
        )
    )
    result = dict(rows.all())
    missing = {"vi", "en"} - result.keys()
    if missing:
        raise RuntimeError(f"Missing required languages: {sorted(missing)}")
    return result


def department_id(bind: sa.Connection, code: str) -> uuid.UUID:
    result = bind.scalar(sa.select(departments.c.id).where(departments.c.code == code))
    if result is None:
        raise RuntimeError(f"Missing required department: {code}")
    return result


def insert_translation_rows(
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
        row = timestamped(
            {
                "id": seed_id(parent_kind, parent_id, "translation", language_code),
                parent_column.name: parent_id,
                "language_id": language_id,
                **values,
            },
            now,
        )
        bind.execute(translation_table.insert().values(**row))


def insert_profile(
    bind: sa.Connection,
    program: dict,
    program_id: uuid.UUID,
    language_map: dict[str, uuid.UUID],
    now: datetime,
) -> None:
    code = program["code"]
    for version in program["profile"]["versions"]:
        year = version["version_year"]
        existing_id = bind.scalar(
            sa.select(program_versions.c.id).where(
                program_versions.c.program_id == program_id,
                program_versions.c.version_year == year,
            )
        )
        if existing_id is not None:
            continue

        version_id = seed_id("program", code, "version", year)
        bind.execute(
            program_versions.insert().values(
                **timestamped(
                    {
                        "id": version_id,
                        "program_id": program_id,
                        "version_year": year,
                        "cohort_code": version.get("cohort_code"),
                        "total_credits": version.get("total_credits"),
                        "is_current": version["is_current"],
                        "is_published": version["is_published"],
                        "sort_order": version["sort_order"],
                    },
                    now,
                )
            )
        )
        insert_translation_rows(
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
            base = {
                key: value for key, value in document.items() if key != "translations"
            }
            bind.execute(
                program_documents.insert().values(
                    **timestamped(
                        {"id": document_id, "version_id": version_id, **base}, now
                    )
                )
            )
            insert_translation_rows(
                bind,
                program_document_translations,
                program_document_translations.c.document_id,
                document_id,
                "document",
                document["translations"],
                language_map,
                now,
            )

        for index, outcome in enumerate(version["outcomes"]):
            outcome_id = seed_id("program", code, "version", year, "outcome", index)
            base = {
                key: value for key, value in outcome.items() if key != "translations"
            }
            bind.execute(
                program_outcomes.insert().values(
                    **timestamped(
                        {"id": outcome_id, "version_id": version_id, **base}, now
                    )
                )
            )
            insert_translation_rows(
                bind,
                program_outcome_translations,
                program_outcome_translations.c.outcome_id,
                outcome_id,
                "outcome",
                outcome["translations"],
                language_map,
                now,
            )

        for index, course in enumerate(version["courses"]):
            course_id = seed_id("program", code, "version", year, "course", index)
            base = {
                key: value for key, value in course.items() if key != "translations"
            }
            bind.execute(
                program_courses.insert().values(
                    **timestamped(
                        {"id": course_id, "version_id": version_id, **base}, now
                    )
                )
            )
            insert_translation_rows(
                bind,
                program_course_translations,
                program_course_translations.c.course_id,
                course_id,
                "course",
                course["translations"],
                language_map,
                now,
            )


def insert_programs(bind: sa.Connection, payload: dict, now: datetime) -> None:
    language_map = language_ids(bind)
    for program in payload["programs"]:
        code = program["code"]
        program_id = bind.scalar(
            sa.select(programs.c.id).where(programs.c.code == code)
        )
        if program_id is None:
            program_id = seed_id("program", code)
            bind.execute(
                programs.insert().values(
                    **timestamped(
                        {
                            "id": program_id,
                            "department_id": department_id(
                                bind, program["department_code"]
                            ),
                            "code": code,
                            "degree_level": program["degree_level"],
                            "duration_years": program["duration_years"],
                            "training_mode": program["training_mode"],
                            "thumbnail_object_key": None,
                            "sort_order": program["sort_order"],
                            "is_active": program["is_active"],
                            "is_published": program["is_published"],
                            "deleted_at": None,
                        },
                        now,
                    )
                )
            )

        for language_code, values in program["translations"].items():
            language_id = language_map.get(language_code)
            if language_id is None:
                continue
            exists = bind.scalar(
                sa.select(program_translations.c.id).where(
                    program_translations.c.program_id == program_id,
                    program_translations.c.language_id == language_id,
                )
            )
            if exists is None:
                bind.execute(
                    program_translations.insert().values(
                        **timestamped(
                            {
                                "id": seed_id(
                                    "program", code, "translation", language_code
                                ),
                                "program_id": program_id,
                                "language_id": language_id,
                                **values,
                            },
                            now,
                        )
                    )
                )

        insert_profile(bind, program, program_id, language_map, now)


def update_menu_parent_links(
    bind: sa.Connection, language_map: dict[str, uuid.UUID], parent_id: uuid.UUID
) -> None:
    training_id = bind.scalar(
        sa.select(menu_items.c.parent_id).where(menu_items.c.id == parent_id)
    )
    parent_links = (
        (training_id, {"vi": "/dao-tao", "en": "/academics"}),
        (
            parent_id,
            {
                "vi": "/dao-tao/dai-hoc",
                "en": "/academics/undergraduate",
            },
        ),
    )
    for item_id, translated_urls in parent_links:
        if item_id is None:
            continue
        bind.execute(
            menu_items.update()
            .where(menu_items.c.id == item_id)
            .values(target_type="EXTERNAL_LINK", target_id=None)
        )
        for language_code, external_url in translated_urls.items():
            language_id = language_map.get(language_code)
            if language_id is None:
                continue
            bind.execute(
                menu_item_translations.update()
                .where(
                    menu_item_translations.c.menu_item_id == item_id,
                    menu_item_translations.c.language_id == language_id,
                )
                .values(external_url=external_url)
            )


def insert_menu_items(bind: sa.Connection, payload: dict, now: datetime) -> None:
    language_map = language_ids(bind)
    menu_id = bind.scalar(sa.select(menus.c.id).where(menus.c.code == "header"))
    if menu_id is None:
        return
    parent_id = bind.scalar(
        sa.select(menu_items.c.id).where(
            menu_items.c.menu_id == menu_id,
            menu_items.c.depth == 2,
            menu_items.c.sort_order == 210,
        )
    )
    if parent_id is None:
        return

    update_menu_parent_links(bind, language_map, parent_id)

    for index, program in enumerate(payload["programs"]):
        code = program["code"]
        vi = program["translations"]["vi"]
        en = program["translations"]["en"]
        translated_values = {
            "vi": {
                "title": vi["name"],
                "external_url": f'/dao-tao/dai-hoc/{vi["slug"]}',
            },
            "en": {
                "title": en["name"],
                "external_url": ("/academics/undergraduate/" + en["slug"]),
            },
        }
        urls = [values["external_url"] for values in translated_values.values()]
        urls.append("/academic-programmes/undergraduate/" + en["slug"])
        item_id = bind.scalar(
            sa.select(menu_items.c.id)
            .join(
                menu_item_translations,
                menu_item_translations.c.menu_item_id == menu_items.c.id,
            )
            .where(
                menu_items.c.parent_id == parent_id,
                menu_item_translations.c.external_url.in_(urls),
            )
            .limit(1)
        )
        if item_id is None:
            item_id = seed_id("undergraduate-menu", code)
            bind.execute(
                menu_items.insert().values(
                    **timestamped(
                        {
                            "id": item_id,
                            "menu_id": menu_id,
                            "parent_id": parent_id,
                            "target_type": "EXTERNAL_LINK",
                            "target_id": None,
                            "open_in_new_tab": False,
                            "depth": 3,
                            "sort_order": 211 + index,
                            "is_visible": True,
                        },
                        now,
                    )
                )
            )

        for language_code, values in translated_values.items():
            language_id = language_map[language_code]
            exists = bind.scalar(
                sa.select(menu_item_translations.c.id).where(
                    menu_item_translations.c.menu_item_id == item_id,
                    menu_item_translations.c.language_id == language_id,
                )
            )
            if exists is None:
                bind.execute(
                    menu_item_translations.insert().values(
                        **timestamped(
                            {
                                "id": seed_id(
                                    "undergraduate-menu",
                                    code,
                                    "translation",
                                    language_code,
                                ),
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
                    .where(menu_item_translations.c.id == exists)
                    .values(**values)
                )


def upgrade() -> None:
    bind = op.get_bind()
    payload = load_seed()
    now = datetime.now(UTC)
    insert_programs(bind, payload, now)
    insert_menu_items(bind, payload, now)


def downgrade() -> None:
    bind = op.get_bind()
    payload = load_seed()

    menu_translation_ids = []
    menu_ids = []
    version_ids = []
    program_translation_ids = []
    program_ids = []
    for program in payload["programs"]:
        code = program["code"]
        menu_ids.append(seed_id("undergraduate-menu", code))
        program_ids.append(seed_id("program", code))
        for language_code in program["translations"]:
            menu_translation_ids.append(
                seed_id("undergraduate-menu", code, "translation", language_code)
            )
            program_translation_ids.append(
                seed_id("program", code, "translation", language_code)
            )
        for version in program["profile"]["versions"]:
            version_ids.append(
                seed_id("program", code, "version", version["version_year"])
            )

    bind.execute(
        menu_item_translations.delete().where(
            menu_item_translations.c.id.in_(menu_translation_ids)
        )
    )
    bind.execute(menu_items.delete().where(menu_items.c.id.in_(menu_ids)))
    bind.execute(
        program_versions.delete().where(program_versions.c.id.in_(version_ids))
    )
    bind.execute(
        program_translations.delete().where(
            program_translations.c.id.in_(program_translation_ids)
        )
    )
    bind.execute(programs.delete().where(programs.c.id.in_(program_ids)))
