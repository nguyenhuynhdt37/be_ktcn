"""Synchronise academic programme links in the header menu."""

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.main import app  # noqa: F401
from app.modules.language.models import Language
from app.modules.menu.models import (
    Menu,
    MenuItem,
    MenuItemTargetType,
    MenuItemTranslation,
)

MENU_ITEMS = (
    (
        "Kỹ thuật Điện tử - Viễn thông",
        "Electronics and Telecommunications Engineering",
        "ky-thuat-dien-tu-vien-thong",
        "electronics-and-telecommunications-engineering",
    ),
    (
        "Kỹ thuật Điều khiển và Tự động hóa",
        "Control and Automation Engineering",
        "ky-thuat-dieu-khien-va-tu-dong-hoa",
        "control-and-automation-engineering",
    ),
    (
        "Công nghệ kỹ thuật Điện - Điện tử",
        "Electrical and Electronic Engineering Technology",
        "cong-nghe-ky-thuat-dien-dien-tu",
        "electrical-and-electronic-engineering-technology",
    ),
    (
        "Công nghệ thông tin",
        "Information Technology",
        "cong-nghe-thong-tin",
        "information-technology",
    ),
    (
        "Công nghệ thông tin chất lượng cao",
        "High-Quality Information Technology",
        "cong-nghe-thong-tin-chat-luong-cao",
        "high-quality-information-technology",
    ),
    (
        "Công nghệ kỹ thuật Ô tô",
        "Automotive Engineering Technology",
        "cong-nghe-ky-thuat-o-to",
        "automotive-engineering-technology",
    ),
    (
        "Công nghệ kỹ thuật Nhiệt",
        "Thermal Engineering Technology",
        "cong-nghe-ky-thuat-nhiet",
        "thermal-engineering-technology",
    ),
    (
        "Kỹ thuật Điện tử và Tin học",
        "Electronic Engineering and Informatics",
        "ky-thuat-dien-tu-va-tin-hoc",
        "electronic-engineering-and-informatics",
    ),
)


async def main() -> None:
    async with SessionLocal() as db:
        menu = (
            await db.execute(select(Menu).where(Menu.code == "header"))
        ).scalar_one()
        languages = {
            language.code: language
            for language in (await db.execute(select(Language))).scalars()
        }

        parent = (
            await db.execute(
                select(MenuItem)
                .join(MenuItemTranslation)
                .join(Language)
                .where(
                    MenuItem.menu_id == menu.id,
                    Language.code == "vi",
                    MenuItemTranslation.title == "Đào tạo đại học",
                )
            )
        ).scalar_one()

        training = (
            await db.execute(
                select(MenuItem)
                .where(MenuItem.id == parent.parent_id)
                .options(
                    selectinload(MenuItem.translations).selectinload(
                        MenuItemTranslation.language
                    )
                )
            )
        ).scalar_one()
        await set_internal_link(
            training,
            {"vi": "/dao-tao", "en": "/academics"},
        )
        await set_internal_link(
            parent,
            {
                "vi": "/dao-tao/dai-hoc",
                "en": "/academics/undergraduate",
            },
        )

        updated_ids = []
        for index, (vi_title, en_title, vi_slug, en_slug) in enumerate(MENU_ITEMS):
            vi_url = f"/dao-tao/dai-hoc/{vi_slug}"
            en_url = f"/academics/undergraduate/{en_slug}"
            legacy_en_url = f"/academic-programmes/undergraduate/{en_slug}"
            item = (
                (
                    await db.execute(
                        select(MenuItem)
                        .join(MenuItemTranslation)
                        .where(
                            MenuItem.menu_id == menu.id,
                            MenuItem.parent_id == parent.id,
                            MenuItemTranslation.external_url.in_(
                                (vi_url, en_url, legacy_en_url)
                            ),
                        )
                        .options(
                            selectinload(MenuItem.translations).selectinload(
                                MenuItemTranslation.language
                            )
                        )
                    )
                )
                .scalars()
                .first()
            )

            if item is None:
                item = MenuItem(
                    menu_id=menu.id,
                    parent_id=parent.id,
                    target_type=MenuItemTargetType.EXTERNAL_LINK,
                    target_id=None,
                    open_in_new_tab=False,
                    depth=3,
                    sort_order=211 + index,
                    is_visible=True,
                )
                db.add(item)
                await db.flush()
            else:
                item.target_type = MenuItemTargetType.EXTERNAL_LINK
                item.target_id = None
                item.open_in_new_tab = False
                item.depth = 3
                item.sort_order = 211 + index
                item.is_visible = True

            existing_translations = (
                await db.execute(
                    select(MenuItemTranslation)
                    .where(MenuItemTranslation.menu_item_id == item.id)
                    .options(selectinload(MenuItemTranslation.language))
                )
            ).scalars()
            existing = {
                translation.language.code: translation
                for translation in existing_translations
                if translation.language
            }
            for code, title, url in (
                ("vi", vi_title, vi_url),
                ("en", en_title, en_url),
            ):
                language = languages.get(code)
                if language is None:
                    continue
                translation = existing.get(code)
                if translation is None:
                    translation = MenuItemTranslation(
                        menu_item_id=item.id,
                        language_id=language.id,
                        title=title,
                        external_url=url,
                    )
                    db.add(translation)
                else:
                    translation.title = title
                    translation.external_url = url
            updated_ids.append(item.id)

        postgraduate = (
            (
                await db.execute(
                    select(MenuItem)
                    .join(MenuItemTranslation)
                    .join(Language)
                    .where(
                        MenuItem.menu_id == menu.id,
                        MenuItem.parent_id == training.id,
                        Language.code == "vi",
                        MenuItemTranslation.title == "Đào tạo sau đại học",
                    )
                    .options(
                        selectinload(MenuItem.translations).selectinload(
                            MenuItemTranslation.language
                        )
                    )
                )
            )
            .scalars()
            .first()
        )
        if postgraduate is None:
            postgraduate = MenuItem(
                menu_id=menu.id,
                parent_id=training.id,
                target_type=MenuItemTargetType.EXTERNAL_LINK,
                target_id=None,
                open_in_new_tab=False,
                depth=2,
                sort_order=220,
                is_visible=True,
            )
            db.add(postgraduate)
            await db.flush()
        await sync_item_translations(
            db,
            postgraduate,
            languages,
            (
                ("vi", "Đào tạo sau đại học", "/dao-tao/sau-dai-hoc"),
                ("en", "Postgraduate education", "/academics/postgraduate"),
            ),
        )

        postgraduate_it = (
            (
                await db.execute(
                    select(MenuItem)
                    .where(
                        MenuItem.menu_id == menu.id,
                        MenuItem.parent_id == postgraduate.id,
                        MenuItem.depth == 3,
                        MenuItem.sort_order == 230,
                    )
                    .options(
                        selectinload(MenuItem.translations).selectinload(
                            MenuItemTranslation.language
                        )
                    )
                )
            )
            .scalars()
            .first()
        )
        if postgraduate_it is None:
            postgraduate_it = MenuItem(
                menu_id=menu.id,
                parent_id=postgraduate.id,
                target_type=MenuItemTargetType.EXTERNAL_LINK,
                target_id=None,
                open_in_new_tab=False,
                depth=3,
                sort_order=230,
                is_visible=True,
            )
            db.add(postgraduate_it)
            await db.flush()
        await sync_item_translations(
            db,
            postgraduate_it,
            languages,
            (
                (
                    "vi",
                    "Thạc sĩ Công nghệ thông tin",
                    "/dao-tao/sau-dai-hoc/thac-si-cong-nghe-thong-tin",
                ),
                (
                    "en",
                    "Master of Information Technology",
                    "/academics/postgraduate/master-of-information-technology",
                ),
            ),
        )

        await db.commit()
        print(
            f"Updated {len(updated_ids)} undergraduate and "
            "1 postgraduate programme menu item"
        )


async def set_internal_link(item: MenuItem, urls: dict[str, str]) -> None:
    item.target_type = MenuItemTargetType.EXTERNAL_LINK
    item.target_id = None
    item.open_in_new_tab = False
    for translation in item.translations:
        if translation.language and translation.language.code in urls:
            translation.external_url = urls[translation.language.code]


async def sync_item_translations(
    db,
    item: MenuItem,
    languages: dict[str, Language],
    values: tuple[tuple[str, str, str], ...],
) -> None:
    item.target_type = MenuItemTargetType.EXTERNAL_LINK
    item.target_id = None
    item.open_in_new_tab = False
    existing = {
        translation.language.code: translation
        for translation in item.translations
        if translation.language
    }
    for language_code, title, url in values:
        language = languages.get(language_code)
        if language is None:
            continue
        translation = existing.get(language_code)
        if translation is None:
            db.add(
                MenuItemTranslation(
                    menu_item_id=item.id,
                    language_id=language.id,
                    title=title,
                    external_url=url,
                )
            )
        else:
            translation.title = title
            translation.external_url = url


if __name__ == "__main__":
    asyncio.run(main())
