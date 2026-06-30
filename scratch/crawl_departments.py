import asyncio
import base64
import uuid
import re
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Department, Position, Staff
from app.modules.article.service import slugify
from app.modules.media.service import MediaService

# Khởi tạo MediaService
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

def parse_name_and_titles(raw_name: str) -> tuple[str | None, str | None, str]:
    """Phân tích học hàm, học vị từ chuỗi tên thô"""
    raw_name = raw_name.strip()
    
    # Sắp xếp các tiền tố học vị/học hàm theo chiều dài giảm dần
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
    """Tải avatar và upload lên MinIO thông qua MediaService"""
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
            content_type = res.headers.get("content-type", "image/jpeg")
            filename = f"avatar-{staff_slug}.png"
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

async def crawl_department_page(db, url: str) -> bool:
    """Cào chi tiết 1 trang bộ môn và nạp dữ liệu vào departments, positions và staffs"""
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
        
    # 1. Xác định tên bộ môn
    department_name = None
    title_p = pblist.find("p")
    if title_p:
        department_name = title_p.text.strip()
    
    if not department_name:
        h2 = soup.find("h2")
        department_name = h2.text.strip() if h2 else "Bộ môn chưa đặt tên"
        
    print(f"\n====== ĐANG XỬ LÝ BỘ MÔN: {department_name} (slug: {slug}) ======")
    
    # 2. Lấy hoặc tạo Department
    dept_stmt = select(Department).where(Department.slug == slug)
    dept_res = await db.execute(dept_stmt)
    department = dept_res.scalars().first()
    
    if not department:
        department = Department(
            name=department_name,
            slug=slug,
            description=f"Bộ môn {department_name} thuộc Viện Kỹ thuật và Công nghệ",
            is_active=True
        )
        db.add(department)
        await db.commit()
        await db.refresh(department)
        print(f"Đã tạo bộ môn mới: {department_name} (ID: {department.id})")
    else:
        print(f"Bộ môn đã tồn tại: {department_name}")
        
    # 3. Lọc danh sách giảng viên trong bộ môn
    staff_blocks = pblist.find_all(class_="ldimg")
    print(f"Tìm thấy {len(staff_blocks)} giảng viên thuộc bộ môn")
    
    for idx, block in enumerate(staff_blocks, 1):
        # Lấy thông tin ảnh
        img_tag = block.find("img")
        avatar_src = img_tag.get("src") if img_tag else None
        
        # Lấy khối link thông tin
        w_link = block.find(class_="w-link")
        if not w_link:
            continue
            
        info_div = w_link.find("div")
        if not info_div:
            continue
            
        # Parse text theo dòng
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
        
        # Kiểm tra sự tồn tại của Staff
        staff_stmt = select(Staff).where(Staff.slug == staff_slug)
        staff_res = await db.execute(staff_stmt)
        staff = staff_res.scalars().first()
        
        # Tải avatar
        avatar_key = None
        if avatar_src:
            avatar_key = await download_and_upload_avatar(db, avatar_src, staff_slug)
            
        if not staff:
            # Tạo cán bộ mới
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
            print(f"   [{idx}] Thêm mới cán bộ: {full_name} ({academic_title or ''} {degree or ''}) - Chức vụ: {position_name}")
        else:
            # Cập nhật thông tin cán bộ
            staff.department_id = department.id
            staff.position_id = position.id
            staff.academic_title = academic_title
            staff.degree = degree
            if avatar_key:
                staff.avatar_object_key = avatar_key
            staff.email = email
            staff.phone = phone
            staff.website = website
            staff.biography = biography
            staff.sort_order = idx
            print(f"   [{idx}] Cập nhật cán bộ: {full_name} ({academic_title or ''} {degree or ''})")
            
        await db.commit()
        
    return True

async def main():
    urls = [
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-ky-thuat-dien-dien-tu",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bm-dieu-khien-tu-dong",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-dien-tu-vien-thong",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-khmt-va-cong-nghe-phan-mem",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-he-thong-va-mang-may-tinh",
        "https://vienktcn.vinhuni.edu.vn/co-cau-to-chuc/bo-mon-cong-nghe-ky-thuat-o-to"
    ]
    
    print("--- BẮT ĐẦU CÀO THÔNG TIN BỘ MÔN VÀ CÁN BỘ ---")
    async with SessionLocal() as db:
        for url in urls:
            try:
                await crawl_department_page(db, url)
            except Exception as e:
                print(f"Lỗi khi cào bộ môn từ {url}: {e}")
            await asyncio.sleep(1.0)
            
    print("\n--- HOÀN THÀNH CÀO THÔNG TIN BỘ MÔN VÀ CÁN BỘ ---")

if __name__ == "__main__":
    asyncio.run(main())
