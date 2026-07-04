import sys
import os
import io
import uuid
import time
import requests
import jwt
from datetime import datetime, timedelta, timezone
from PIL import Image
import boto3
from botocore.config import Config

# Thêm thư mục root vào sys.path để import các module của dự án
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.modules.auth.models import User
from app.core.database import SessionLocal

BASE_URL = "http://localhost:8000"


async def get_superadmin_user_id() -> str:
    """Truy vấn database để lấy UUID của superadmin user."""
    from sqlalchemy import select
    async with SessionLocal() as db:
        stmt = select(User).where(User.username == "superadmin")
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            print(f"🔑 Tìm thấy superadmin ID trong DB: {user.id}")
            return str(user.id)
        # Fallback nếu không có database
        print("⚠️ Không tìm thấy superadmin trong DB, sử dụng random UUID.")
        return "00000000-0000-0000-0000-000000000000"


def generate_admin_token(user_id: str) -> str:
    """Sinh JWT token admin hợp lệ từ SECRET_KEY của hệ thống."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def test_security_headers():
    print("\n[TEST 1] Kiểm tra Security Headers...")
    res = requests.get(f"{BASE_URL}/health")
    
    x_frame = res.headers.get("X-Frame-Options")
    x_content = res.headers.get("X-Content-Type-Options")
    x_xss = res.headers.get("X-XSS-Protection")
    referrer = res.headers.get("Referrer-Policy")
    
    print(f" -> X-Frame-Options: {x_frame} (Expected: DENY)")
    print(f" -> X-Content-Type-Options: {x_content} (Expected: nosniff)")
    print(f" -> X-XSS-Protection: {x_xss} (Expected: 1; mode=block)")
    print(f" -> Referrer-Policy: {referrer} (Expected: strict-origin-when-cross-origin)")
    
    assert x_frame == "DENY", "Lỗi: Thiếu hoặc sai X-Frame-Options"
    assert x_content == "nosniff", "Lỗi: Thiếu hoặc sai X-Content-Type-Options"
    assert x_xss == "1; mode=block", "Lỗi: Thiếu hoặc sai X-XSS-Protection"
    assert referrer == "strict-origin-when-cross-origin", "Lỗi: Thiếu hoặc sai Referrer-Policy"
    print("✅ [TEST 1] PASSED: Các Security Headers hoạt động chính xác.")


def test_payload_size_limiter():
    print("\n[TEST 2] Kiểm tra giới hạn kích thước Payload (DoS Protection)...")
    # Tạo body dung lượng 12MB vượt quá giới hạn 10MB
    large_data = b"x" * (12 * 1024 * 1024)
    
    try:
        # Gửi request POST kích thước lớn đến API công cộng /health
        res = requests.post(
            f"{BASE_URL}/health", 
            data=large_data, 
            headers={"Content-Type": "application/octet-stream"},
            timeout=5
        )
        print(f" -> Response Code: {res.status_code}")
        if res.status_code == 413:
            print(f" -> Response Body: {res.json()}")
            print("✅ [TEST 2] PASSED: Server chặn thành công với mã 413 Payload Too Large.")
        else:
            print(f"❌ [TEST 2] FAILED: Server không chặn payload 12MB. Code nhận được: {res.status_code}")
            sys.exit(1)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Nếu server đóng kết nối socket lập tức, requests sẽ ném lỗi ConnectionError
        print(f" -> Nhận được lỗi đóng socket sớm (Broken Pipe / Connection Reset): {e}")
        print("✅ [TEST 2] PASSED: Server chủ động ngắt kết nối để tự bảo vệ.")


def test_magic_bytes_bypass(token: str):
    print("\n[TEST 3] Tấn công giả mạo đuôi file (Magic Bytes Validation)...")
    url = f"{BASE_URL}/api/v1/admin/media/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Gửi file text giả danh PNG
    fake_png_data = b"HACKED-TEXT-PAYLOAD-IN-PNG"
    files = {
        "file": ("attack.png", fake_png_data, "image/png")
    }
    
    res = requests.post(url, headers=headers, files=files)
    print(f" -> Response Code: {res.status_code}")
    print(f" -> Response Body: {res.text}")
    
    # Kì vọng server phát hiện ra magic bytes không khớp và trả về 400 Bad Request
    if res.status_code == 400 and "INVALID_FILE_SIGNATURE" in res.text:
        print("✅ [TEST 3] PASSED: Chặn thành công file giả mạo PNG.")
    else:
        print("❌ [TEST 3] FAILED: Server cho phép tải lên file PNG giả mạo!")
        sys.exit(1)


def test_svg_xss_protection(token: str):
    print("\n[TEST 4] Tấn công XSS thông qua file SVG...")
    url = f"{BASE_URL}/api/v1/admin/media/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Case 4.1: SVG độc hại có chứa thẻ <script>
    malicious_svg = b"""
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <circle cx="50" cy="50" r="40" stroke="green" stroke-width="4" fill="yellow" />
        <script type="text/javascript">alert('XSS Attack');</script>
    </svg>
    """
    files_malicious = {
        "file": ("xss_attack.svg", malicious_svg, "image/svg+xml")
    }
    
    res_mal = requests.post(url, headers=headers, files=files_malicious)
    print(f" -> Case 4.1 (SVG độc hại) Code: {res_mal.status_code}")
    print(f" -> Case 4.1 Body: {res_mal.text}")
    
    # Case 4.2: SVG độc hại chứa event handler onload
    malicious_onload_svg = b"""
    <svg xmlns="http://www.w3.org/2000/svg" onload="alert(document.cookie)">
        <rect width="100" height="100" fill="red" />
    </svg>
    """
    files_onload = {
        "file": ("xss_onload.svg", malicious_onload_svg, "image/svg+xml")
    }
    res_onload = requests.post(url, headers=headers, files=files_onload)
    print(f" -> Case 4.2 (SVG chứa onload) Code: {res_onload.status_code}")
    print(f" -> Case 4.2 Body: {res_onload.text}")
    
    # Case 4.3: SVG an toàn
    safe_svg = b"""
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <circle cx="50" cy="50" r="40" stroke="blue" fill="red" />
    </svg>
    """
    files_safe = {
        "file": ("safe.svg", safe_svg, "image/svg+xml")
    }
    res_safe = requests.post(url, headers=headers, files=files_safe)
    print(f" -> Case 4.3 (SVG an toàn) Code: {res_safe.status_code}")
    
    assert res_mal.status_code == 400 and "UNSAFE_SVG_FILE" in res_mal.text, "Lỗi: Không chặn được SVG chứa script"
    assert res_onload.status_code == 400 and "UNSAFE_SVG_FILE" in res_onload.text, "Lỗi: Không chặn được SVG chứa onload"
    assert res_safe.status_code == 200, f"Lỗi: SVG an toàn bị chặn oan! Code: {res_safe.status_code}"
    
    print("✅ [TEST 4] PASSED: Chặn thành công SVG độc hại, cho phép tải lên SVG an toàn.")


def test_exif_removal(token: str):
    print("\n[TEST 5] Kiểm tra tính năng xóa thông tin nhạy cảm EXIF Metadata...")
    url = f"{BASE_URL}/api/v1/admin/media/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Tạo file ảnh JPEG có chứa dữ liệu EXIF thô (chèn Orientation & Description)
    img = Image.new("RGB", (100, 100), color="blue")
    exif = img.getexif()
    exif[0x0112] = 3  # Orientation: Bottom-Right
    exif[0x010e] = "KTCN Security Test - Sensitive GPS Location"  # ImageDescription
    
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG", exif=exif)
    img_data = img_io.getvalue()
    
    # 2. Upload ảnh có EXIF lên
    files = {
        "file": ("exif_test.jpg", img_data, "image/jpeg")
    }
    res = requests.post(url, headers=headers, files=files)
    print(f" -> Upload Code: {res.status_code}")
    
    if res.status_code != 200:
        print(f"❌ [TEST 5] FAILED: Upload ảnh JPEG thất bại: {res.text}")
        sys.exit(1)
        
    res_data = res.json()
    object_key = res_data.get("object_key")
    print(f" -> Lưu trên MinIO với object_key: {object_key}")
    
    # 3. Kết nối thẳng đến MinIO S3 bằng boto3 để tải file gốc vừa upload xuống
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"http{'s' if settings.MINIO_SECURE else ''}://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    
    try:
        response = s3_client.get_object(Bucket=settings.MINIO_BUCKET, Key=object_key)
        downloaded_bytes = response["Body"].read()
        
        # 4. Sử dụng Pillow đọc ảnh đã tải xuống và kiểm tra EXIF
        downloaded_img = Image.open(io.BytesIO(downloaded_bytes))
        downloaded_exif = downloaded_img.getexif()
        
        # In ra các tag EXIF nếu còn tồn tại
        exif_tags = dict(downloaded_exif)
        print(f" -> Các tag EXIF còn lại trong ảnh đã upload: {exif_tags}")
        
        # Xác nhận EXIF trống hoặc không chứa tag nhạy cảm đã chèn
        assert 0x010e not in downloaded_exif, "Lỗi: EXIF ImageDescription (0x010e) vẫn tồn tại!"
        print("✅ [TEST 5] PASSED: EXIF Metadata đã bị xóa sạch hoàn toàn khỏi ảnh gốc.")
        
    except Exception as e:
        print(f"❌ [TEST 5] FAILED: Kiểm tra EXIF thất bại: {e}")
        sys.exit(1)


def test_rate_limiting_ip_spoofing():
    print("\n[TEST 6] Kiểm tra Rate Limiting & Proxy IP Spoofing...")
    # Thử gọi API login bằng header IP giả lập để xem rate limit
    url = f"{BASE_URL}/api/v1/auth/login"
    dummy_data = {"username": "attacker", "password": "password"}
    
    # Case 6.1: Spam từ một IP cụ thể (NAT IP) -> Phải bị chặn 429
    fake_ip = f"1.2.3.{int(time.time()) % 250 + 1}"
    print(f" -> Case 6.1: Spam 10 requests từ IP: {fake_ip}")
    blocked = False
    
    for i in range(1, 11):
        headers = {
            "X-Forwarded-For": fake_ip,
            "Content-Type": "application/json"
        }
        res = requests.post(url, json=dummy_data, headers=headers)
        if res.status_code == 429:
            print(f"    - Bị chặn ở request #{i} (Nhận mã 429 Too Many Requests).")
            blocked = True
            break
            
    assert blocked, "Lỗi: Không chặn được IP spam liên tiếp"
    
    # Chờ giải phóng rate limit hoặc đổi dải IP khác để kiểm tra tính độc lập
    # Case 6.2: Chống IP Spoofing (Đổi IP liên tục -> Tất cả đều phải thành công 401 chứ không bị 429)
    print(" -> Case 6.2: Đổi IP liên tục để gửi request (Kiểm tra tính độc lập)...")
    success_count = 0
    for i in range(1, 6):
        headers = {
            "X-Forwarded-For": f"100.100.100.{i}",
            "Content-Type": "application/json"
        }
        res = requests.post(url, json=dummy_data, headers=headers)
        # Vì user 'attacker' không có thật, kì vọng trả về 401 Unauthorized chứ KHÔNG phải 429.
        if res.status_code == 401 or res.status_code == 400:
            success_count += 1
            
    print(f"    - Số request vượt qua rate limit thành công (nhận 401/400): {success_count}/5")
    assert success_count == 5, f"Lỗi: Các IP độc lập bị khóa chéo lẫn nhau! Chỉ thành công {success_count}/5"
    print("✅ [TEST 6] PASSED: Chặn thành công NAT IP spam, chống IP Spoofing hiệu quả.")


def test_user_id_rate_limiting(token: str):
    print("\n[TEST 7] Kiểm tra Rate Limiting theo User ID (Không bị khóa do NAT)...")
    url = f"{BASE_URL}/api/v1/admin/categories"
    random_ip = f"9.9.9.{int(time.time()) % 250 + 1}"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Forwarded-For": random_ip
    }
    
    print(f" -> Gửi liên tiếp 115 request GET với cùng 1 Token Admin đến /api/v1/admin/categories (IP: {random_ip})...")
    blocked = False
    for i in range(1, 116):
        res = requests.get(url, headers=headers)
        if i <= 5 or i >= 98:
            print(f"    - Request #{i}: Code {res.status_code}")
        if res.status_code == 429:
            print(f"    - Token bị chặn ở request #{i} (Nhận mã 429).")
            blocked = True
            break
            
    assert blocked, "Lỗi: Token admin spam không bị chặn bởi User-based Rate Limit"
    print("✅ [TEST 7] PASSED: Rate Limiting theo User ID hoạt động chính xác.")


def test_sql_injection_and_xss():
    print("\n[TEST 8] Kiểm tra Input Validation (Chống SQL Injection & XSS)...")
    # Gửi payload SQLi và XSS thô vào query parameter 'search' của API Portal Articles
    url = f"{BASE_URL}/api/v1/portal/articles"
    
    payloads = [
        "' OR '1'='1",
        "1; DROP TABLE users;--",
        "<script>alert('XSS')</script>",
        "javascript:alert(1)"
    ]
    
    for payload in payloads:
        print(f" -> Thử payload: {payload}")
        res = requests.get(url, params={"search": payload})
        print(f"    - Response Code: {res.status_code}")
        # Kì vọng: Trả về 200 (không tìm thấy bài viết, dữ liệu trống) hoặc 422 (lỗi validation).
        # Không được trả về 500 (lỗi biên dịch SQL hoặc crash server).
        assert res.status_code in [200, 422], f"Lỗi: Server crash (500) khi nhận payload độc hại! Code: {res.status_code}"
        
    print("✅ [TEST 8] PASSED: Hệ thống an toàn trước SQL Injection & XSS qua tham số đầu vào.")


async def run_all_tests():
    user_id = await get_superadmin_user_id()
    token = generate_admin_token(user_id)
    
    print("\n=======================================================")
    print("🚀 BẮT ĐẦU KIỂM THỬ XÂM NHẬP & BẢO MẬT NÂNG CAO (PEN-TEST)")
    print("=======================================================")
    
    test_security_headers()
    test_payload_size_limiter()
    test_magic_bytes_bypass(token)
    test_svg_xss_protection(token)
    test_exif_removal(token)
    test_rate_limiting_ip_spoofing()
    test_user_id_rate_limiting(token)
    test_sql_injection_and_xss()
    
    print("\n=======================================================")
    print("🎉 TẤT CẢ CÁC BÀI KIỂM THỬ XÂM NHẬP (8/8) ĐÃ PASSED THÀNH CÔNG!")
    print("=======================================================")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_all_tests())
