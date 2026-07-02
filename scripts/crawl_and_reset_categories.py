import asyncio
import sys
import os
import re
from loguru import logger
from sqlalchemy import delete, select

# Thêm root dự án vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.category.models import Category, CategoryTranslation
from app.modules.language.models import Language
from app.modules.translation.service import translation_service
from app.modules.translation.schemas.common import TranslationContext
from app.shared.ai.config import get_active_model, save_active_model


def slugify(text: str) -> str:
    """Chuyển đổi văn bản sang dạng slug không dấu tiếng Việt."""
    text = text.lower()
    text = text.replace('_', '-')
    patterns = {
        '[àáảãạăằắẳẵặâầấẩẫậ]': 'a',
        '[èéẻẽẹêềếểễệ]': 'e',
        '[ìíỉĩị]': 'i',
        '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
        '[ùúủũụưừứửữự]': 'u',
        '[ỳýỷỹỵ]': 'y',
        'đ': 'd'
    }
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


# Cây danh mục chuẩn của website Viện Kỹ thuật và Công nghệ (https://vienktcn.vinhuni.edu.vn/)
CATEGORIES_STRUCTURE = [
    {
        "name": "Giới thiệu",
        "slug": "gioi-thieu",
        "children": [
            {"name": "Lịch sử phát triển", "slug": "lich-su-phat-trien"},
            {"name": "Chức năng, nhiệm vụ", "slug": "chuc-nang-nhiem-vu"}
        ]
    },
    {
        "name": "Cơ cấu tổ chức",
        "slug": "co-cau-to-chuc",
        "children": [
            {"name": "Ban lãnh đạo Viện", "slug": "ban-lanh-dao-vien"},
            {"name": "Hội đồng khoa học và đào tạo", "slug": "hoi-dong-khoa-hoc-va-dao-tao"},
            {
                "name": "Các bộ môn",
                "slug": "cac-bo-mon",
                "children": [
                    {"name": "Kỹ thuật điện - điện tử", "slug": "bo-mon-ky-thuat-dien-dien-tu"},
                    {"name": "Kỹ thuật điều khiển và tự động hóa", "slug": "bo-mon-ky-thuat-dieu-khien-tu-dong-hoa"},
                    {"name": "Điện tử Viễn thông", "slug": "bo-mon-dien-tu-vien-thong"},
                    {"name": "Khoa học máy tính và CN phần mềm", "slug": "bo-mon-khmt-va-cong-nghe-phan-mem"},
                    {"name": "Hệ thống và Mạng máy tính", "slug": "bo-mon-he-thong-va-mang-may-tinh"},
                    {"name": "Bộ môn Công nghệ kỹ thuật Ô tô", "slug": "bo-mon-cong-nghe-ky-thuat-o-to"}
                ]
            },
            {
                "name": "Các tổ chức đoàn thể",
                "slug": "cac-to-chuc-doan-the",
                "children": [
                    {"name": "Công đoàn", "slug": "cong-doan"},
                    {"name": "Đoàn thanh niên và Hội sinh viên", "slug": "doan-thanh-nien-va-hoi-sinh-vien"}
                ]
            }
        ]
    },
    {
        "name": "Đào tạo",
        "slug": "dao-tao",
        "children": [
            {
                "name": "Đào tạo đại học",
                "slug": "dao-tao-dai-hoc",
                "children": [
                    {"name": "Ngành Kỹ thuật Điện tử-Viễn thông", "slug": "nganh-ky-thuat-dien-tu-vien-thong"},
                    {"name": "Ngành Kỹ thuật Điều khiển và Tự động hóa", "slug": "nganh-ky-thuat-dieu-khien-va-tu-dong-hoa"},
                    {"name": "Ngành Công nghệ kỹ thuật Điện - Điện tử", "slug": "nganh-cong-nghe-ky-thuat-dien-dien-tu"},
                    {"name": "Ngành Công nghệ thông tin", "slug": "nganh-cong-nghe-thong-tin"},
                    {"name": "Ngành Công nghệ thông tin Hệ Chất lượng cao", "slug": "nganh-cong-nghe-thong-tin-chat-luong-cao"},
                    {"name": "Ngành Công nghệ kỹ thuật Ô tô", "slug": "nganh-cong-nghe-ky-thuat-o-to"},
                    {"name": "Ngành Công nghệ kỹ thuật Nhiệt (Chuyên ngành Nhiệt lạnh)", "slug": "nganh-cong-nghe-ky-thuat-nhiet-dien-lanh"},
                    {"name": "Ngành Kỹ thuật Điện tử và Tin học", "slug": "nganh-ky-thuat-dien-tu-va-tin-hoc"}
                ]
            },
            {
                "name": "Đào tạo sau đại học",
                "slug": "dao-tao-sau-dai-hoc",
                "children": [
                    {"name": "Ngành Thạc sỹ Công nghệ thông tin", "slug": "nganh-thac-sy-cong-nghe-thong-tin"}
                ]
            }
        ]
    },
    {
        "name": "Nghiên cứu khoa học",
        "slug": "nghien-cuu-khoa-hoc",
        "children": [
            {"name": "Các hướng nghiên cứu", "slug": "cac-huong-nghien-cuu"},
            {"name": "Phòng thực hành, thí nghiệm", "slug": "phong-thuc-hanh-thi-nghiem"},
            {"name": "Đề tài nghiên cứu", "slug": "de-tai-nghien-cuu"},
            {"name": "Các công trình đã công bố", "slug": "cac-cong-trinh-da-cong-bo"}
        ]
    },
    {
        "name": "Tuyển sinh",
        "slug": "tuyen-sinh",
        "children": [
            {"name": "Cao học Công nghệ thông tin", "slug": "tuyen-sinh-cao-hoc-cong-nghe-thong-tin"},
            {
                "name": "Đại học chính quy",
                "slug": "tuyen-sinh-dai-hoc-chinh-quy",
                "children": [
                    {"name": "Ngành Kỹ thuật Điện tử, Viễn thông", "slug": "tuyen-sinh-nganh-ky-thuat-dien-tu-vien-thong"},
                    {"name": "Ngành KT Điều khiển và Tự động hóa", "slug": "tuyen-sinh-nganh-ky-thuat-dieu-khien-va-tu-dong-hoa"},
                    {"name": "Ngành Công nghệ KT Điện, Điện tử", "slug": "tuyen-sinh-nganh-cong-nghe-ky-thuat-dien-dien-tu"},
                    {"name": "Ngành Công nghệ thông tin", "slug": "tuyen-sinh-nganh-cong-nghe-thong-tin"},
                    {"name": "Ngành CNTT Chất lượng cao", "slug": "tuyen-sinh-nganh-cong-nghe-thong-tin-chat-luong-cao"},
                    {"name": "Ngành Công nghệ Kỹ thuật Ôtô", "slug": "tuyen-sinh-nganh-cong-nghe-ky-thuat-o-to"},
                    {"name": "Ngành Công nghệ KT Nhiệt (CN Nhiệt lạnh)", "slug": "tuyen-sinh-nganh-cong-nghe-ky-thuat-nhiet-dien-lanh"}
                ]
            }
        ]
    },
    {
        "name": "Sinh viên",
        "slug": "sinh-vien",
        "children": [
            {"name": "Văn bản, biểu mẫu", "slug": "van-ban-bieu-mau"},
            {"name": "Thông tin học bổng", "slug": "thong-tin-hoc-bong"},
            {"name": "Thông tin việc làm", "slug": "thong-tin-viec-lam"},
            {"name": "Cựu sinh viên", "slug": "cuu-sinh-vien"}
        ]
    },
    {
        "name": "Tin tức và Sự kiện",
        "slug": "tin-tuc-va-su-kien"
    }
]


# Tập hợp các slug đã sử dụng để tránh lỗi Unique Constraints
used_slugs = set()

def get_unique_slug(base_slug: str, lang_code: str) -> str:
    """Trả về slug duy nhất cho ngôn ngữ tương ứng."""
    slug = base_slug
    counter = 1
    key = f"{lang_code}:{slug}"
    while key in used_slugs:
        slug = f"{base_slug}-{counter}"
        key = f"{lang_code}:{slug}"
        counter += 1
    used_slugs.add(key)
    return slug


def extract_names(nodes):
    """Trích xuất tất cả các name từ cây danh mục thành list phẳng không trùng lặp."""
    names = []
    for node in nodes:
        names.append(node["name"])
        if "children" in node:
            names.extend(extract_names(node["children"]))
    return list(set(names))


async def crawl_and_reset():
    # Lưu và đổi active model tạm thời sang gemini-2.5-flash để đảm bảo dịch thành công
    old_model = get_active_model()
    logger.info(f"⚙️ Tạm thời đổi model từ {old_model} sang gemini-2.5-flash để tránh lỗi 401/429...")
    save_active_model("gemini-2.5-flash")

    try:
        async with SessionLocal() as db:
            logger.info("🗑️ 1. Tiến hành xóa cứng toàn bộ danh mục và các bản dịch liên quan...")
            
            # Xóa CategoryTranslation trước
            await db.execute(delete(CategoryTranslation))
            # Xóa Category sau
            await db.execute(delete(Category))
            await db.flush()
            
            logger.info("🌐 2. Truy vấn thông tin ngôn ngữ trong database...")
            # Lấy thông tin ngôn ngữ vi và en
            vi_lang_stmt = select(Language).where(Language.code == "vi")
            en_lang_stmt = select(Language).where(Language.code == "en")
            
            vi_lang = (await db.execute(vi_lang_stmt)).scalar_one_or_none()
            en_lang = (await db.execute(en_lang_stmt)).scalar_one_or_none()
            
            if not vi_lang:
                logger.error("❌ Không tìm thấy ngôn ngữ tiếng Việt (code='vi') trong database.")
                return
            if not en_lang:
                logger.error("❌ Không tìm thấy ngôn ngữ tiếng Anh (code='en') trong database.")
                return
                
            logger.info(f"✅ Đã cấu hình ngôn ngữ: vi (ID: {vi_lang.id}), en (ID: {en_lang.id})")
            
            logger.info("🌐 3. Trích xuất danh sách tên danh mục tiếng Việt để dịch batch...")
            vietnamese_names = extract_names(CATEGORIES_STRUCTURE)
            
            logger.info(f"🤖 4. Đang dịch batch {len(vietnamese_names)} tên danh mục sang tiếng Anh qua OmniRoute...")
            try:
                batch_res = await translation_service.translate_batch(
                    texts=vietnamese_names,
                    target_languages=["en"],
                    context=TranslationContext.CATEGORY_NAME
                )
                # Tạo map: {"Giới thiệu": "Introduction", ...}
                translation_map = {}
                for item in batch_res:
                    translation_map[item["vi"]] = item.get("en", item["vi"])
            except Exception as e:
                logger.error(f"❌ Lỗi khi dịch batch: {e}. Fallback về sử dụng tên gốc.")
                translation_map = {name: name for name in vietnamese_names}

            logger.info("⚡ 5. Bắt đầu gieo hạt dữ liệu danh mục...")

            async def insert_category_node(item_data, parent_id=None, sort_order=0):
                # Tạo Category mới
                category = Category(
                    parent_id=parent_id,
                    sort_order=sort_order,
                    status="PUBLISHED",
                    is_visible=True
                )
                db.add(category)
                await db.flush()  # sinh category.id
                
                # Tạo translation tiếng Việt
                vi_slug = get_unique_slug(item_data["slug"], "vi")
                vi_trans = CategoryTranslation(
                    category_id=category.id,
                    language_id=vi_lang.id,
                    name=item_data["name"],
                    slug=vi_slug,
                    description=f"Danh mục {item_data['name']}"
                )
                db.add(vi_trans)
                
                # Lấy tên dịch tiếng Anh từ map
                en_name = translation_map.get(item_data["name"], item_data["name"])
                en_slug = get_unique_slug(slugify(en_name), "en")
                
                # Tạo translation tiếng Anh
                en_trans = CategoryTranslation(
                    category_id=category.id,
                    language_id=en_lang.id,
                    name=en_name,
                    slug=en_slug,
                    description=f"Category {en_name}"
                )
                db.add(en_trans)
                
                logger.info(f"   [+] Danh mục: '{item_data['name']}' ➔ '{en_name}' (slug: {en_slug})")
                
                # Xử lý các con đệ quy
                if "children" in item_data and item_data["children"]:
                    for child_idx, child_data in enumerate(item_data["children"]):
                        await insert_category_node(child_data, parent_id=category.id, sort_order=child_idx)

            # Duyệt và insert các danh mục gốc
            for root_idx, root_data in enumerate(CATEGORIES_STRUCTURE):
                await insert_category_node(root_data, parent_id=None, sort_order=root_idx)
                
            await db.commit()
            logger.info("🎉 Quá trình xóa và gieo hạt danh mục Viện KTCN đã hoàn thành thành công!")
    finally:
        logger.info(f"⚙️ Khôi phục lại model active cũ: {old_model}...")
        save_active_model(old_model)


if __name__ == "__main__":
    asyncio.run(crawl_and_reset())
