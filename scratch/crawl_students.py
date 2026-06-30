import asyncio
import base64
import uuid
import re
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.article.models import Article, ArticleStatus
from app.modules.article.service import slugify
from app.modules.category.models import Category
from app.modules.auth.models import User
from app.modules.media.service import MediaService
from app.shared.seo.helper import resolve_seo

# Khởi tạo MediaService
media_service = MediaService()

async def get_or_create_category(db, name: str, slug: str) -> Category:
    """Lấy hoặc tạo danh mục theo tên và slug"""
    stmt = select(Category).where(Category.slug == slug)
    res = await db.execute(stmt)
    category = res.scalars().first()
    if not category:
        category = Category(
            name=name,
            slug=slug,
            description=f"Danh mục chứa các bài viết thuộc chủ đề {name}",
            status="PUBLISHED",
            is_visible=True
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        print(f"Đã tạo mới danh mục: '{name}' (slug: {slug})")
    return category

async def get_default_author(db) -> uuid.UUID:
    """Lấy ID của người dùng đầu tiên để làm tác giả"""
    stmt = select(User.id)
    res = await db.execute(stmt)
    user_id = res.scalars().first()
    return user_id

async def process_images_in_content(db, soup_content, title_slug: str) -> tuple[list[str], str]:
    """
    Tìm các thẻ img trong nội dung, decode base64 hoặc tải link URL, upload lên MinIO,
    và thay thế src bằng link nội bộ.
    """
    uploaded_keys = []
    thumbnail_key = None
    
    imgs = soup_content.find_all("img")
    for idx, img in enumerate(imgs):
        src = img.get("src", "")
        if not src:
            continue
            
        file_content = None
        content_type = "image/png"
        filename = f"{title_slug}-img-{idx}.png"
        
        # 1. Xử lý ảnh dạng base64
        if src.startswith("data:image"):
            try:
                header, encoded = src.split(",", 1)
                file_content = base64.b64decode(encoded)
                match = re.search(r"data:(image/\w+);base64", header)
                if match:
                    content_type = match.group(1)
            except Exception as e:
                print(f"   Lỗi decode base64 ảnh {idx}: {e}")
                continue
        # 2. Xử lý ảnh dạng link thông thường
        elif src.startswith("http") or src.startswith("/"):
            try:
                img_url = src if src.startswith("http") else f"https://vienktcn.vinhuni.edu.vn{src}"
                async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
                    img_res = await client.get(img_url)
                    if img_res.status_code == 200:
                        file_content = img_res.content
                        content_type = img_res.headers.get("content-type", "image/jpeg")
                        url_filename = img_url.split("/")[-1].split("?")[0]
                        if url_filename:
                            filename = url_filename
            except Exception as e:
                print(f"   Lỗi tải ảnh {src}: {e}")
                continue
                
        # 3. Tiến hành upload lên MinIO thông qua MediaService
        if file_content:
            try:
                media_item = await media_service.upload_file(
                    db=db,
                    file_content=file_content,
                    filename=filename,
                    content_type=content_type
                )
                
                # Tạo URL MinIO nội bộ thay thế src gốc của img
                new_src = f"http://localhost:9000/university-media/{media_item.object_key}"
                img["src"] = new_src
                
                uploaded_keys.append(media_item.object_key)
                if not thumbnail_key:
                    thumbnail_key = media_item.object_key
            except Exception as e:
                print(f"   Lỗi upload ảnh {filename} lên MinIO: {e}")
                
    return uploaded_keys, thumbnail_key

async def crawl_article_detail(db, url: str, category_name: str, category_slug: str, author_id: uuid.UUID) -> bool:
    """Cào chi tiết 1 bài viết sinh viên và nạp vào DB. Trả về True nếu thành công, False nếu bỏ qua/lỗi."""
    url_parts = url.split("/")
    raw_slug = url_parts[-1] if url_parts[-1] else url_parts[-2]
    
    # Chuẩn hóa slug
    title_slug = slugify(raw_slug)
    
    # Kiểm tra xem bài viết đã tồn tại chưa
    stmt = select(Article.id).where(Article.slug == title_slug)
    res = await db.execute(stmt)
    existing_id = res.scalars().first()
    if existing_id:
        print(f"-> Bỏ qua: Bài viết đã tồn tại trong DB (slug: {title_slug})")
        return False
        
    print(f"-> Đang cào sinh viên: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            print(f"   Lỗi tải trang chi tiết, status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   Lỗi kết nối đến trang chi tiết: {e}")
        return False
        
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 1. Parse Title
    title = None
    detail_post = soup.find(class_="detail-post")
    if detail_post:
        h1 = detail_post.find("h1")
        if h1:
            title = h1.text.strip()
            
    if not title:
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "Bài viết sinh viên không có tiêu đề"
        
    # 2. Parse Ngày đăng
    publish_date = datetime.now(timezone.utc)
    date_tag = soup.find(class_="post-subinfo")
    if date_tag:
        date_text = date_tag.text.strip()
        match = re.search(r"(\d{2}:\d{2})\s+(\d{2}/\d{2}/\d{4})", date_text)
        if match:
            time_part, date_part = match.groups()
            try:
                from datetime import timedelta
                ict_tz = timezone(timedelta(hours=7))
                dt_naive = datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M")
                publish_date = dt_naive.replace(tzinfo=ict_tz)
            except Exception as e:
                print(f"   Lỗi parse datetime {date_text}: {e}")
                
    # 3. Parse Content
    content_div = soup.find(class_="post-content")
    if not content_div and detail_post:
        content_div = detail_post
        
    if not content_div:
        print("   Không tìm thấy phần thân bài viết class 'post-content'")
        return False
        
    # 4. Xử lý ảnh trong bài viết
    uploaded_keys, thumbnail_key = await process_images_in_content(db, content_div, title_slug)
    
    # 5. Lấy content HTML sau khi đã thay thế link ảnh
    content_html = str(content_div)
    
    # Tạo excerpt ngắn
    text_content = content_div.get_text()
    text_content = re.sub(r"\s+", " ", text_content).strip()
    excerpt = text_content[:200] + "..." if len(text_content) > 200 else text_content
    
    # 6. Chuẩn hóa SEO sử dụng helper dự án
    thumbnail_url = f"http://localhost:9000/university-media/{thumbnail_key}" if thumbnail_key else None
    seo_data = resolve_seo(
        title=title,
        description=excerpt,
        content=text_content,
        thumbnail_url=thumbnail_url,
        slug=title_slug
    )
    
    # 7. Lấy Category tương ứng
    category = await get_or_create_category(db, category_name, category_slug)
    
    # 8. Lưu mới bài viết vào database
    new_article = Article(
        title=title,
        slug=title_slug,
        excerpt=excerpt,
        content=content_html,
        thumbnail_object_key=thumbnail_key,
        category_id=category.id,
        author_id=author_id,
        status=ArticleStatus.PUBLISHED,
        is_draft=False,
        publish_at=publish_date,
        published_at=publish_date,
        # SEO
        seo_title=seo_data.seo_title,
        seo_description=seo_data.seo_description,
        robots=seo_data.seo_robots,
        canonical_url=seo_data.seo_canonical,
        og_title=title,
        og_description=excerpt,
        og_image=seo_data.seo_og_image_url
    )
    db.add(new_article)
    await db.commit()
    print(f"   Thành công: Đã lưu bài viết sinh viên mới vào DB (slug: {title_slug})")
    return True

async def get_article_links_from_page(page_url: str) -> list[tuple[str, str, str]]:
    """Tải một trang danh sách sinh viên và trả về danh sách (url, category_name, category_slug)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(page_url, headers=headers)
        if response.status_code != 200:
            print(f"Lỗi tải trang danh sách {page_url}: status {response.status_code}")
            return []
    except Exception as e:
        print(f"Lỗi kết nối trang danh sách {page_url}: {e}")
        return []
        
    soup = BeautifulSoup(response.content, "html.parser")
    links = []
    
    # Tìm các thẻ a chứa link bài viết có /seo/
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/seo/" in href:
            abs_url = href if href.startswith("http") else f"https://vienktcn.vinhuni.edu.vn{href}"
            
            # Mặc định của trang này là Sinh viên
            category_name = "Sinh viên"
            category_slug = "sinh-vien"
            
            if "/sinh-vien/seo/" in abs_url:
                category_name = "Sinh viên"
                category_slug = "sinh-vien"
            elif "/thong-bao/seo/" in abs_url:
                category_name = "Thông báo"
                category_slug = "thong-bao"
            elif "/dao-tao/seo/" in abs_url:
                category_name = "Đào tạo"
                category_slug = "dao-tao"
            elif "/tuyen-sinh/seo/" in abs_url:
                category_name = "Tuyển sinh"
                category_slug = "tuyen-sinh"
                
            links.append((abs_url, category_name, category_slug))
            
    seen = set()
    unique_links = []
    for item in links:
        if item[0] not in seen:
            seen.add(item[0])
            unique_links.append(item)
            
    return unique_links

async def main():
    max_pages = 5  # Giới hạn cào 5 trang danh sách sinh viên
    base_list_url = "https://vienktcn.vinhuni.edu.vn/sinh-vien"
    
    print(f"--- BẮT ĐẦU PIPELINE CRAWLER SINH VIÊN (Giới hạn: {max_pages} trang danh sách) ---")
    
    all_links = []
    for page in range(1, max_pages + 1):
        if page == 1:
            page_url = base_list_url
        else:
            page_url = f"{base_list_url}/page/{page}"
            
        print(f"Đang quét trang danh sách sinh viên {page}/{max_pages}: {page_url} ...")
        links = await get_article_links_from_page(page_url)
        print(f"Tìm thấy {len(links)} link sinh viên ở trang {page}")
        all_links.extend(links)
        
    seen_urls = set()
    final_links = []
    for item in all_links:
        if item[0] not in seen_urls:
            seen_urls.add(item[0])
            final_links.append(item)
            
    print(f"\nTổng số bài viết sinh viên duy nhất tìm thấy: {len(final_links)}")
    
    async with SessionLocal() as db:
        author_id = await get_default_author(db)
        if not author_id:
            print("Không tìm thấy người dùng nào trong DB để gán author_id!")
            return
            
        success_count = 0
        skip_count = 0
        
        for idx, (url, cat_name, cat_slug) in enumerate(final_links, 1):
            print(f"\n[{idx}/{len(final_links)}] Processing...")
            try:
                success = await crawl_article_detail(db, url, cat_name, cat_slug, author_id)
                if success:
                    success_count += 1
                else:
                    skip_count += 1
            except Exception as e:
                print(f"   Lỗi khi xử lý bài viết sinh viên {url}: {e}")
                skip_count += 1
                
            await asyncio.sleep(1.0)
            
    print(f"\n--- HOÀN THÀNH CÀO SINH VIÊN ---")
    print(f"Tổng số bài viết sinh viên xử lý: {len(final_links)}")
    print(f"Nạp mới thành công: {success_count}")
    print(f"Bỏ qua (đã tồn tại hoặc lỗi): {skip_count}")

if __name__ == "__main__":
    asyncio.run(main())
