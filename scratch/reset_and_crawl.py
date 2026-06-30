import asyncio
import base64
import uuid
import re
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, delete

from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Department, Position, Staff
from app.modules.article.service import slugify
from app.modules.media.service import MediaService

media_service = MediaService()

def decode_cloudflare_email(cf_string: str) -> str:
    """Giải mã email được obfuscate bởi Cloudflare"""
    try:
        key = int(cf_string[:2], 16)
        email = ""
        for i in range(2, len(cf_string), 2):
            char_code = int(cf_string[i:i+2], 16) ^ key
            email += chr(char_code)
        return email
    except Exception:
        return ""

def detect_image_mime_type(content: bytes, default: str = "image/png") -> str:
    """Xác định MIME type thật sự của ảnh bằng Magic Bytes"""
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return "image/gif"
    elif content.startswith(b"RIFF") and b"WEBP" in content[8:12]:
        return "image/webp"
    return default

def parse_name_and_titles(raw_name: str) -> tuple[str | None, str | None, str]:
    """Phân tích học hàm, học vị từ chuỗi tên thô"""
    raw_name = raw_name.strip()
    prefixes = [
        "PGS.TS.NCS.", "PGS.TS.NCS", "PGS.TS.", "PGS. TS.", "PGS.TS", 
        "GS.TS.", "GS. TS.", "GS.TS", "ThS.NCS.", "ThS.NCS", "ThS. NCS.", 
        "TS.NCS.", "TS.NCS", "PGS.", "GS.", "TS.", "TS", "ThS.", "ThS", 
        "CN.", "KS."
    ]
    academic_title = None
    degree = None
    name = raw_name
    
    for pref in prefixes:
        if raw_name.startswith(pref):
            if "PGS" in pref:
                academic_title = "PGS"
            elif "GS" in pref:
                academic_title = "GS"
                
            if "TS" in pref:
                if "NCS" in pref:
                    degree = "TS.NCS"
                else:
                    degree = "TS"
            elif "ThS" in pref:
                if "NCS" in pref:
                    degree = "ThS.NCS"
                else:
                    degree = "ThS"
            elif "CN" in pref:
                degree = "CN"
            elif "KS" in pref:
                degree = "KS"
                
            name = raw_name[len(pref):].strip()
            if name.startswith("."):
                name = name[1:].strip()
            break
            
    return academic_title, degree, name

async def get_or_create_position(db, name: str) -> Position:
    """Lấy hoặc tạo chức vụ trong bảng positions"""
    name = name.strip()
    stmt = select(Position).where(Position.name == name)
    res = await db.execute(stmt)
    position = res.scalars().first()
    
    if not position:
        position = Position(
            name=name,
            description=f"Chức vụ công tác {name}",
            is_active=True
        )
        db.add(position)
        await db.commit()
        await db.refresh(position)
        print(f"   Đã tạo chức vụ mới: '{name}'")
    return position

async def download_and_upload_avatar(db, src_url: str, staff_slug: str) -> str | None:
    """Tải avatar và upload lên MinIO thông qua MediaService với định dạng MIME chuẩn"""
    if not src_url:
        return None
        
    img_url = src_url if src_url.startswith("http") else f"https://vienktcn.vinhuni.edu.vn{src_url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            res = await client.get(img_url, headers=headers)
        if res.status_code == 200:
            content_type = detect_image_mime_type(res.content)
            ext = "jpg" if "jpeg" in content_type else "png"
            filename = f"avatar-{staff_slug}.{ext}"
            
            media_item = await media_service.upload_file(
                db=db,
                file_content=res.content,
                filename=filename,
                content_type=content_type
            )
            return media_item.object_key
    except Exception as e:
        print(f"   Lỗi tải/upload avatar {img_url}: {e}")
    return None

async def reset_database(db):
    """Xoá sạch dữ liệu trong 3 bảng staffs, departments, positions"""
    print("\n--- BẮT ĐẦU RESET DATABASE (3 BẢNG: STAFFS, DEPARTMENTS, POSITIONS) ---")
    try:
        # Xoá staffs trước để tránh lỗi khoá ngoại RESTRICT/CASCADE
        await db.execute(delete(Staff))
        print("1. Đã xoá sạch bảng staffs")
        
        # Xoá departments
        await db.execute(delete(Department))
        print("2. Đã xoá sạch bảng departments")
        
        # Xoá positions
        await db.execute(delete(Position))
        print("3. Đã xoá sạch bảng positions")
        
        await db.commit()
        print("--- RESET DATABASE THÀNH CÔNG ---\n")
    except Exception as e:
        await db.rollback()
        print(f"Lỗi khi reset database: {e}")
        raise e

async def crawl_department_page(db, url: str) -> bool:
    """Cào chi tiết 1 trang bộ môn và nạp dữ liệu sạch vào database"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    slug = url.split("/")[-1] if url.split("/")[-1] else url.split("/")[-2]
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Lỗi tải trang bộ môn {url}: status {response.status_code}")
            return False
    except Exception as e:
        print(f"Lỗi kết nối trang bộ môn {url}: {e}")
        return False
        
    soup = BeautifulSoup(response.content, "html.parser")
    
    pblist = soup.find(class_="pblist")
    if not pblist:
        print(f"Không tìm thấy thẻ 'pblist' chứa danh sách cán bộ tại {url}")
        return False
        
    # Xác định tên bộ môn
    department_name = None
    title_p = pblist.find("p")
    if title_p:
        department_name = title_p.text.strip()
    if not department_name:
        h2 = soup.find("h2")
        department_name = h2.text.strip() if h2 else slug.replace("-", " ").title()
        
    print(f"\n====== ĐANG CÀO BỘ MÔN: {department_name} (slug: {slug}) ======")
    
    # Tạo mới bộ môn
    department = Department(
        name=department_name,
        slug=slug,
        description=f"Bộ môn {department_name} thuộc Viện Kỹ thuật và Công nghệ",
        is_active=True
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)
    
    # Lọc danh sách giảng viên trong bộ môn
    staff_blocks = pblist.find_all(class_="ldimg")
    print(f"Tìm thấy {len(staff_blocks)} giảng viên thuộc bộ môn")
    
    for idx, block in enumerate(staff_blocks, 1):
        img_tag = block.find("img")
        avatar_src = img_tag.get("src") if img_tag else None
        
        w_link = block.find(class_="w-link")
        if not w_link:
            continue
            
        info_div = w_link.find("div")
        if not info_div:
            continue
            
        lines = [line.strip() for line in info_div.get_text(separator="\n").split("\n") if line.strip()]
        if not lines:
            continue
            
        raw_name = lines[0]
        academic_title, degree, full_name = parse_name_and_titles(raw_name)
        staff_slug = slugify(full_name)
        
        # Xác định chức vụ
        position_name = "Giảng viên"
        if len(lines) > 1:
            line_2 = lines[1]
            if not any(k in line_2.lower() for k in ["email", "điện thoại", "phone", "trang cá nhân", "nhiệm vụ"]):
                position_name = line_2
                
        # Parse Email, điện thoại và website
        email = None
        phone = None
        website = None
        
        # Giải mã email bằng Cloudflare
        cf_email_tag = info_div.find("a", class_="__cf_email__")
        if cf_email_tag and cf_email_tag.get("data-cfemail"):
            email = decode_cloudflare_email(cf_email_tag["data-cfemail"])
            
        # Parse Điện thoại
        phone_match = re.search(r"(?:Điện thoại|Phone):\s*([0-9\.\s]+)", info_div.text, re.IGNORECASE)
        if phone_match:
            phone = phone_match.group(1).strip()
            
        # Parse Trang cá nhân
        web_a = info_div.find("a", href=True)
        if web_a and "email-protection" not in web_a["href"] and "javascript" not in web_a["href"] and web_a.text.strip() != "Chi tiết":
            website = web_a["href"]
            
        # Parse Biography (Nhiệm vụ chi tiết)
        biography = None
        biography_div = w_link.find(class_="ptrach")
        if biography_div:
            biography = biography_div.text.strip()
            
        # Ghi nhận chức vụ
        position = await get_or_create_position(db, position_name)
        
        # Tải/upload avatar với định dạng ảnh chuẩn
        avatar_key = None
        if avatar_src:
            avatar_key = await download_and_upload_avatar(db, avatar_src, staff_slug)
            
        # Tạo mới cán bộ giảng viên (không cần check trùng vì database vừa được reset sạch)
        staff = Staff(
            department_id=department.id,
            position_id=position.id,
            full_name=full_name,
            slug=staff_slug,
            academic_title=academic_title,
            degree=degree,
            avatar_object_key=avatar_key,
            email=email,
            phone=phone,
            website=website,
            biography=biography,
            sort_order=idx,
            is_active=True
        )
        db.add(staff)
        print(f"   [{idx}] Đã nạp cán bộ: {full_name} ({academic_title or ''} {degree or ''}) - Chức danh: {position_name}")
        await db.commit()
        
    return True

async def main():
    # Danh sách các trang bộ môn gốc trên website của trường
    urls = [
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-ky-thuat-dien-dien-tu",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bm-dieu-khien-tu-dong",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-dien-tu-vien-thong",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-khmt-va-cong-nghe-phan-mem",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-he-thong-va-mang-may-tinh",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-cong-nghe-ky-thuat-o-to"
    ]
    
    async with SessionLocal() as db:
        # Bước 1: Reset dữ liệu 3 bảng
        await reset_database(db)
        
        # Bước 2: Tiến hành cào mới hoàn toàn
        print("\n--- BẮT ĐẦU CÀO LẠI TOÀN BỘ DỮ LIỆU MỚI SẠCH SẼ ---")
        for url in urls:
            try:
                await crawl_department_page(db, url)
            except Exception as e:
                print(f"Lỗi khi cào bộ môn từ {url}: {e}")
            await asyncio.sleep(1.0)
            
    print("\n--- HOÀN THÀNH PIPELINE RESET & CRAWL LẠI ---")

if __name__ == "__main__":
    asyncio.run(main())
