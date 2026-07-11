"""Idempotently connect official department menu items to department records."""

import asyncio
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.main  # noqa: F401 - register every SQLAlchemy model
from app.core.database import SessionLocal
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.menu.models import Menu, MenuItem, MenuItemTargetType, MenuItemTranslation


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def is_automation(value: str) -> bool:
    normalized = normalize(value)
    return "dieu khien" in normalized and "tu dong" in normalized


async def main() -> None:
    async with SessionLocal() as db:
        menu = (await db.execute(select(Menu).where(Menu.code == "header"))).scalar_one()
        items = list(
            (
                await db.execute(
                    select(MenuItem)
                    .where(MenuItem.menu_id == menu.id)
                    .options(selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language))
                )
            ).scalars()
        )
        departments = list(
            (
                await db.execute(
                    select(Department)
                    .where(
                        Department.deleted_at.is_(None),
                        Department.is_active.is_(True),
                        Department.unit_type == "department",
                    )
                    .options(selectinload(Department.translations).selectinload(DepartmentTranslation.language))
                )
            ).scalars()
        )

        parent = next(
            item
            for item in items
            if any(normalize(trans.title) == "cac bo mon" for trans in item.translations)
        )
        automation_department = next(
            department
            for department in departments
            if any(is_automation(trans.name) for trans in department.translations)
        )

        changed = 0
        for item in items:
            if item.parent_id != parent.id or item.target_id is not None:
                continue
            if any(is_automation(trans.title) for trans in item.translations):
                item.target_type = MenuItemTargetType.DEPARTMENT
                item.target_id = automation_department.id
                item.external_url = None
                changed += 1

        await db.commit()
        print(f"Synchronized {changed} department menu link(s).")


if __name__ == "__main__":
    asyncio.run(main())
