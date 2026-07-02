import asyncio
import sys
import os
import re
import requests
import base64
import uuid
import hashlib
import time
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy import delete, select

# Tắt warning SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thêm root dự án vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.config import settings
from app.modules.article.models import Article, ArticleTranslation, ArticleStatus
from app.modules.category.models import Category, CategoryTranslation
from app.modules.language.models import Language
from app.modules.tag.models import Tag
from app.modules.auth.models import User
from app.modules.media.service import MediaService
media_service = MediaService()
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


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_with_retry(url: str, retries: int = 3, delay: int = 2, timeout: int = 15):
    """GET request có retry. Nếu gặp lỗi 404 thì ngừng retry ngay lập tức vì ảnh/trang chắc chắn không tồn tại."""
    for i in range(retries):
        try:
            resp = requests.get(url, headers=headers, verify=False, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 404:
                logger.warning(f"   ❌ Tải {url[:50]}... gặp lỗi 404 Not Found. Không thử lại.")
                return resp
            logger.warning(f"   ⚠️ Tải {url[:50]}... thất bại (Status: {resp.status_code}). Thử lại lần {i+1}/{retries}...")
        except Exception as e:
            logger.warning(f"   ⚠️ Lỗi kết nối tải {url[:50]}...: {e}. Thử lại lần {i+1}/{retries}...")
        if i < retries - 1:
            time.sleep(delay)
    return None


# Tập hợp các slug đã sử dụng để tránh trùng lặp Unique Constraint
used_slugs = set()

def get_unique_slug(base_slug: str, lang_code: str) -> str:
    slug = base_slug
    counter = 1
    key = f"{lang_code}:{slug}"
    while key in used_slugs:
        slug = f"{base_slug}-{counter}"
        key = f"{lang_code}:{slug}"
        counter += 1
    used_slugs.add(key)
    return slug


# Cache để tránh upload trùng lặp cùng một ảnh nhiều lần
uploaded_images_cache = {}


# Khóa Lock để tuần tự hóa các ghi chép vào Database trên cùng một AsyncSession
db_lock = asyncio.Lock()


async def download_and_upload_to_minio(db, img_src: str, sem: asyncio.Semaphore) -> str:
    """Download ảnh từ URL hoặc decode từ Base64, sau đó upload lên MinIO và trả về link public."""
    img_src = img_src.strip()
    if not img_src:
        return ""
        
    if img_src in uploaded_images_cache:
        return uploaded_images_cache[img_src]
        
    async with sem:
        try:
            file_content = None
            content_type = "image/jpeg"
            filename = "image.jpg"
            
            # 1. Xử lý ảnh dạng Base64 (chuỗi base64 dài)
            if img_src.startswith("data:"):
                pattern = re.compile(r'^data:(image/[a-zA-Z0-9+.-]+);base64,(.*)$')
                match = pattern.match(img_src)
                if match:
                    content_type = match.group(1)
                    base64_data = match.group(2)
                    file_content = base64.b64decode(base64_data)
                    ext = content_type.split("/")[-1]
                    filename = f"base64_img_{uuid.uuid4().hex[:8]}.{ext}"
            
            # 2. Xử lý ảnh dạng URL (tuyệt đối hoặc tương đối)
            else:
                url = img_src
                if not url.startswith("http"):
                    url = "https://vienktcn.vinhuni.edu.vn" + (url if url.startswith("/") else "/" + url)
                
                resp = get_with_retry(url, retries=3, delay=1.5, timeout=12)
                if resp and resp.status_code == 200:
                    file_content = resp.content
                    content_type = resp.headers.get("Content-Type", "image/jpeg")
                    filename = url.split("/")[-1] or "image.jpg"
                    if "?" in filename:
                        filename = filename.split("?")[0]
            
            if file_content:
                # Sử dụng lock để tránh việc flush đồng thời trên cùng một session DB gây lỗi Unique PKey
                async with db_lock:
                    # Upload lên MinIO thông qua media_service của backend
                    media_item = await media_service.upload_file(
                        db=db,
                        file_content=file_content,
                        filename=filename,
                        content_type=content_type
                    )
                    # Lấy public link hiển thị của ảnh trong MinIO (build trực tiếp từ settings)
                    protocol = "https" if settings.MINIO_SECURE else "http"
                    public_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{media_item.bucket or settings.MINIO_BUCKET}/{media_item.object_key}"
                    uploaded_images_cache[img_src] = public_url
                    logger.info(f"   📸 [MinIO Upload] Thành công: {img_src[:50]}... ➔ {public_url}")
                    return public_url
        except Exception as e:
            logger.error(f"Lỗi khi upload ảnh {img_src[:50]}... lên MinIO: {e}")
            
    return img_src  # Fallback: Nếu lỗi, giữ nguyên link gốc


async def process_html_images(db, content_html: str, sem: asyncio.Semaphore):
    """Quét toàn bộ ảnh trong nội dung HTML, upload lên MinIO và thay thế thuộc tính src."""
    soup = BeautifulSoup(content_html, "html.parser")
    img_tags = soup.find_all("img")
    
    if not img_tags:
        return content_html, None
        
    tasks = []
    matched_tags = []
    
    for img in img_tags:
        src = img.get("src")
        if src:
            tasks.append(download_and_upload_to_minio(db, src, sem))
            matched_tags.append(img)
            
    if tasks:
        # Chạy upload song song các ảnh để tăng tốc
        uploaded_urls = await asyncio.gather(*tasks)
        for img_tag, public_url in zip(matched_tags, uploaded_urls):
            if public_url:
                img_tag["src"] = public_url
                
        # Lấy ảnh đầu tiên upload thành công lên MinIO làm thumbnail (tránh lấy link lỗi 404 làm thumbnail)
        first_thumbnail = None
        for url in uploaded_urls:
            if url and (url.startswith("http://") or url.startswith("https://")) and settings.MINIO_ENDPOINT in url:
                # Trích xuất key tương đối để lưu vào DB (ví dụ: files/xxxx thay vì chứa cả domain localhost:9000)
                # Vì schema đã tự động build URL đầy đủ rồi nên trong DB ta chỉ nên lưu object key tương đối!
                # Điều này giúp link ảnh không bị hardcode IP/Domain trong DB và chạy được trên mọi môi trường!
                parts = url.split(f"/{settings.MINIO_BUCKET}/")
                if len(parts) > 1:
                    first_thumbnail = parts[1]
                else:
                    first_thumbnail = url
                break
        return str(soup), first_thumbnail
        
    return content_html, None


async def collect_all_news_links() -> list:
    """Quét qua toàn bộ phân trang chuyên mục tin tức để gom hết các bài viết thực tế."""
    page = 1
    all_links = []
    seen_links = set()
    
    # Quét tối đa 12 trang phân trang (đầy đủ các bài viết của chuyên mục)
    max_pages = 12
    
    logger.info("🕸️ Bắt đầu quét danh sách phân trang chuyên mục Tin tức và Sự kiện...")
    while page <= max_pages:
        url = "https://vienktcn.vinhuni.edu.vn/tin-tuc-va-su-kien"
        if page > 1:
            url = f"https://vienktcn.vinhuni.edu.vn/tin-tuc-va-su-kien/page/{page}"
            
        logger.info(f"   [{page}/{max_pages}] Quét trang danh sách: {url}")
        try:
            resp = get_with_retry(url, retries=3, delay=2.0, timeout=15)
            if not resp or resp.status_code != 200:
                logger.warning(f"Không thể tải trang {page}. Dừng quét.")
                break
                
            soup = BeautifulSoup(resp.content, "html.parser")
            page_links = []
            
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if "/tin-tuc-va-su-kien/seo/" in href or ("/seo/" in href and "tin-tuc-va-su-kien" in href):
                    if not href.startswith("http"):
                        href = "https://vienktcn.vinhuni.edu.vn" + (href if href.startswith("/") else "/" + href)
                    if href not in seen_links:
                        seen_links.add(href)
                        page_links.append(href)
                        all_links.append(href)
                        
            logger.info(f"      Tìm thấy {len(page_links)} bài viết ở trang {page}.")
            if not page_links:
                break
                
            page += 1
        except Exception as e:
            logger.error(f"Lỗi khi quét trang danh sách {page}: {e}")
            break
            
    logger.info(f"🕸️ Quét sitemap hoàn tất! Tìm thấy tổng cộng {len(all_links)} bài viết thực tế cần cào.")
    return all_links


def parse_article_detail(url: str):
    """Tải và parse chi tiết tiêu đề, tóm tắt và HTML của bài viết."""
    try:
        resp = get_with_retry(url, retries=3, delay=1.5, timeout=15)
        if not resp or resp.status_code != 200:
            return None
            
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Tiêu đề
        h1 = soup.find("h1", class_="post-title") or soup.find("h1")
        if not h1:
            return None
        title = h1.text.strip()
        if not title:
            return None
            
        # Nội dung HTML chi tiết
        content_div = soup.find("div", class_="post-content") or soup.find("div", class_="content")
        if not content_div:
            content_div = soup.find("div", id=lambda x: x and "ContentPane" in x)
            
        if not content_div:
            return None
            
        content_html = str(content_div)
        content_text = content_div.text.strip()
        
        # Tóm tắt
        excerpt_div = soup.find("div", class_="post-summary")
        excerpt = excerpt_div.text.strip() if excerpt_div else ""
        if not excerpt:
            excerpt = content_text[:200].replace("\n", " ").strip() + "..."
            
        # Trích xuất ngày xuất bản
        publish_date = None
        subinfo_span = soup.find("span", class_="post-subinfo")
        if subinfo_span:
            date_str = subinfo_span.text.strip()
            try:
                match = re.search(r'(\d{1,2}):(\d{1,2})\s+(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
                if match:
                    hour, minute, day, month, year = map(int, match.groups())
                    publish_date = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
            except Exception as e:
                logger.error(f"Lỗi parse ngày xuất bản '{date_str}' từ {url}: {e}")

        return {
            "title": title,
            "excerpt": excerpt,
            "content_html": content_html,
            "publish_date": publish_date
        }
    except Exception as e:
        logger.error(f"Lỗi parse chi tiết bài viết {url}: {e}")
        return None


async def crawl_and_reset_articles():
    # Lưu và đổi active model tạm thời sang gemini-2.5-flash để đảm bảo dịch thành công
    old_model = get_active_model()
    logger.info(f"⚙️ Tạm thời đổi model từ {old_model} sang gemini-2.5-flash...")
    save_active_model("gemini-2.5-flash")

    try:
        # 1. Thu thập toàn bộ link bài viết từ sitemap/phân trang
        article_urls = await collect_all_news_links()
        
        if not article_urls:
            logger.error("❌ Không thể kết nối hoặc quét được bài viết nào từ website Viện KTCN. Tiến trình dừng lại.")
            return

        # Chỉ cào tối đa 60 bài viết mới nhất để đảm bảo không bị nghẽn mạng quá lâu
        article_urls = article_urls[:60]
        logger.info(f"📝 Bắt đầu crawl chi tiết thực tế của {len(article_urls)} bài viết...")

        # 2. Xóa sạch DB cũ trước tiên
        async with SessionLocal() as db:
            logger.info("🗑️ 1. Xóa toàn bộ bài viết và bản dịch cũ trong DB...")
            await db.execute(delete(ArticleTranslation))
            await db.execute(delete(Article))
            await db.commit()

            # Lấy thông tin ngôn ngữ và danh mục Tin tức dưới dạng ID nguyên bản (UUID) để tránh lỗi lazy load/expire
            vi_lang = (await db.execute(select(Language).where(Language.code == "vi"))).scalar_one_or_none()
            en_lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one_or_none()
            
            if not vi_lang or not en_lang:
                logger.error("❌ Thiếu ngôn ngữ vi hoặc en trong database.")
                return
                
            vi_lang_id = vi_lang.id
            en_lang_id = en_lang.id

            cat_stmt = select(CategoryTranslation).where(
                CategoryTranslation.slug == "tin-tuc-va-su-kien",
                CategoryTranslation.language_id == vi_lang_id
            )
            cat_trans = (await db.execute(cat_stmt)).scalar_one_or_none()
            category_id = cat_trans.category_id if cat_trans else None
            
            if not category_id:
                # Fallback lấy category đầu tiên
                first_cat = (await db.execute(select(Category))).scalars().first()
                category_id = first_cat.id if first_cat else None

        # Khởi tạo Semaphore cho upload ảnh
        sem = asyncio.Semaphore(5)

        # 3. Vòng lặp crawl và lưu trực tiếp từng bài viết thực tế
        for idx, url in enumerate(article_urls):
            logger.info(f"   👉 [{idx+1}/{len(article_urls)}] Đang xử lý bài viết: {url}")
            
            # Tải chi tiết bài viết thực tế
            art_data = parse_article_detail(url)
            if not art_data:
                logger.warning(f"      ⚠️ Bỏ qua bài viết '{url}' do không thể tải chi tiết.")
                continue
                
            vi_title = art_data["title"]
            vi_excerpt = art_data["excerpt"]
            
            async with SessionLocal() as db:
                try:
                    # Dịch tiêu đề & tóm tắt sang tiếng Anh qua AI (có timeout 8s)
                    en_title = vi_title
                    en_excerpt = vi_excerpt
                    
                    try:
                        en_title_res = await asyncio.wait_for(
                            translation_service.translate_text(
                                text=vi_title,
                                target_languages=["en"],
                                context=TranslationContext.ARTICLE_TITLE
                            ),
                            timeout=8.0
                        )
                        en_title = en_title_res.get("en", vi_title)
                    except Exception as e:
                        logger.warning(f"      [AI-Warning] Không thể dịch tiêu đề '{vi_title[:30]}...': {e}. Fallback gán bản gốc.")

                    try:
                        en_excerpt_res = await asyncio.wait_for(
                            translation_service.translate_text(
                                text=vi_excerpt,
                                target_languages=["en"],
                                context=TranslationContext.ARTICLE_SUMMARY
                            ),
                            timeout=8.0
                        )
                        en_excerpt = en_excerpt_res.get("en", vi_excerpt)
                    except Exception as e:
                        logger.warning(f"      [AI-Warning] Không thể dịch tóm tắt: {e}. Fallback gán bản gốc.")

                    # Tải và upload ảnh (bao gồm Base64) thực tế lên MinIO, cập nhật HTML
                    logger.info("      📸 Đang xử lý và tải ảnh lên MinIO...")
                    processed_html, thumbnail_url = await process_html_images(db, art_data["content_html"], sem)
                    
                    # Ghi trực tiếp bài viết vào Database và commit ngay
                    pub_date = art_data.get("publish_date") or datetime.now(timezone.utc)
                    
                    # Tạo Article
                    article = Article(
                        category_id=category_id,
                        thumbnail_object_key=thumbnail_url,
                        status=ArticleStatus.PUBLISHED,
                        is_draft=False,
                        publish_at=pub_date,
                        published_at=pub_date
                    )
                    db.add(article)
                    await db.flush()

                    # Bản dịch tiếng Việt
                    vi_slug = get_unique_slug(slugify(vi_title), "vi")
                    vi_trans = ArticleTranslation(
                        article_id=article.id,
                        language_id=vi_lang_id,
                        title=vi_title,
                        slug=vi_slug,
                        excerpt=vi_excerpt,
                        content=processed_html
                    )
                    db.add(vi_trans)

                    # Bản dịch tiếng Anh (Không dịch HTML để tăng tốc, chỉ dịch tiêu đề/tóm tắt)
                    en_slug = get_unique_slug(slugify(en_title), "en")
                    en_trans = ArticleTranslation(
                        article_id=article.id,
                        language_id=en_lang_id,
                        title=en_title,
                        slug=en_slug,
                        excerpt=en_excerpt,
                        content=processed_html  # Giữ nguyên HTML tiếng Việt
                    )
                    db.add(en_trans)

                    await db.commit()
                    logger.info(f"      💾 [DB Commit] Đã lưu thành công bài viết thực tế: '{vi_title}'")

                except Exception as ex:
                    logger.error(f"      ❌ Lỗi khi lưu bài viết: {ex}")
                    await db.rollback()

        logger.info("🎉 Quá trình crawl bài viết thực tế và lưu trữ đã hoàn tất thành công!")
    finally:
        logger.info(f"⚙️ Khôi phục lại model active cũ: {old_model}...")
        save_active_model(old_model)


if __name__ == "__main__":
    asyncio.run(crawl_and_reset_articles())
