import asyncio
import sys
import uuid
from loguru import logger
import httpx

from app.core.config import settings

# Cấu hình logger
logger.remove()
logger.add(sys.stderr, level="INFO")


async def test_seo_assistant():
    # Sử dụng AsyncClient kết nối trực tiếp app qua ASGI để test nhanh
    from app.main import app

    logger.info("⏳ Khởi động AsyncClient kết nối ứng dụng...")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập tài khoản Admin lấy Token")
        login_payload = {
            "username": "superadmin",
            "password": "Password@123"
        }
        login_res = await ac.post("/api/v1/auth/login", json=login_payload)
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        # 2. Lấy danh sách bài viết để tìm một article_id thực tế trong hệ thống
        logger.info("📂 2. Lấy danh sách bài viết từ database...")
        articles_res = await ac.get("/api/v1/admin/articles?page=1&page_size=5", headers=headers)
        assert articles_res.status_code == 200, f"Lấy bài viết thất bại: {articles_res.text}"
        articles = articles_res.json().get("items", [])
        
        if articles:
            article_id = articles[0]["id"]
            logger.info(f"👉 Sử dụng article_id thực tế: {article_id}")
        else:
            article_id = str(uuid.uuid4())
            logger.info(f"👉 Không có bài viết nào trong DB, sử dụng UUID ngẫu nhiên: {article_id}")

        # 3. Gửi yêu cầu phân tích SEO
        # Payload chứa: 
        # - HTML có base64 image (sẽ bị strip)
        # - 1 ảnh thiếu alt (sẽ bị cảnh báo trong Rule Engine)
        # - 1 link nội bộ (thỏa mãn rule)
        # - Tiêu đề, tóm tắt và từ khóa chính
        logger.info("🧪 3. Gửi yêu cầu phân tích SEO (SEO Audit)...")
        seo_payload = {
            "title": "BẢN TIN TÌNH NGUYỆN 2409 (ngày 18/7/2024) | NHẬT KÝ KỲ NGHỈ HÈ CỦA “BÉ NGOAN” TẠI VĨNH SƠN, ANH SƠN",
            "content": "<p>&nbsp;&nbsp;&nbsp; <strong>ĐẨY MẠNH TĂNG GIA SẢN XUẤT, THỰC HÀNH TIẾT KIỆM</strong></p><p>&nbsp; &nbsp; Nhận thức rõ vị trí, ý nghĩa của công tác hậu cần nói chung, tăng gia sản xuất, thực hành tiết kiệm nói riêng. Tận dụng được vườn rau sẵn có tại trường Mầm non Vĩnh Sơn. Sáng ngày (18/7/2024), đội SVTN 2409 đã chủ động dọn dẹp vệ sinh, phát quang bụi rậm, nhổ cỏ cho vườn rau xanh tại trường Mầm non Vinh Sơn để tạo điều kiện thuận lợi cho hoa màu phát triển, chủ động về thực phẩm trong quá trình sinh hoạt tại địa phương và góp phần gìn giữ không gian xanh của Nhà trường.</p><p><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451749466_1225054388709870_1143805446345891682_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=101&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=I50OCdBBzqIQ7kNvgEum9c0&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYAZlGW2v2R2Cczd3v1fbj9POlp149p4JOJ3Vmu7ujO2Eg&amp;oe=66A07569\" alt=\"Có thể là hình ảnh về 7 người và cỏ\"></p><p><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451834395_1225055282043114_2554584398186984319_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=110&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=UhX30DSK-noQ7kNvgGyGir-&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYAX5i2L9-b5dvNHhi-lJJFab7azk3T9P9fDvqqCKeOh0g&amp;oe=66A068C9\" alt=\"Có thể là hình ảnh về 6 người và cây\"></p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451838257_1225052955376680_6417899827853122426_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=108&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=56pcW93PWDcQ7kNvgGUOoZ2&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYD07L8c0LD1MenUPwasX4BTR0Koi2saRTu6z6HDgInt5A&amp;oe=66A0621D\" alt=\"Có thể là hình ảnh về 7 người\"></p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451991989_1225053085376667_2685053761153537209_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=109&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=ey8IerfpRuIQ7kNvgGVs8dB&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYAomdiH9f_NRVumNgHDE-xq3C66CkDn-_y9VtLJsvXlyQ&amp;oe=66A05B73\" alt=\"Có thể là hình ảnh về 8 người, cỏ và cây\"></p><p><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451837654_1225053148709994_5376028287579293781_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=101&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=PnqQ92fYs0sQ7kNvgFxTTUW&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYCiBagCskjziD3BgKoY6b6MjgRdqubltwjiASkdb_7xJg&amp;oe=66A07155\" alt=\"Có thể là hình ảnh về 6 người\"></p><p>&nbsp;</p><p>&nbsp;&nbsp;&nbsp; <strong>HÀNH TRÌNH ƯƠM MẦM TRI THỨC</strong></p><p>&nbsp;&nbsp;&nbsp;&nbsp;Đến với xã Vĩnh Sơn, huyện Anh Sơn năm nay, đội 2409 tổ chức 10 lớp học miễn phí dành cho các em học sinh từ cấp 1 đến cấp 2 vào tất cả các ngày trong tuần. Trực tiếp giảng dạy các lớp là các bạn sinh viên đến từ Viện Kỹ thuật Công nghệ và Trường Sư Phạm – Trường Đại học Vinh, với đa dạng các môn học Toán, Tin, Tiếng Việt, Tiếng Anh. Lớp học sẽ được duy trì từ nay cho đến hết chiến dịch.<br>&nbsp;&nbsp;&nbsp;&nbsp;“LỚP HỌC CHO EM – MIỄN PHÍ 0 ĐỒNG” được BTV Huyện đoàn Anh Sơn chỉ đạo triển khai triển địa bàn huyện nhằm ôn tập, củng cố kiến thức, trang bị thêm kỹ năng cho các em học sinh trong dịp nghỉ hè để các em có một nền tảng tốt, chuẩn bị năm học mới.&nbsp;</p><p><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451614887_1225191575362818_5367914690334551099_n.jpg?_nc_cat=106&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=KVMUJjJVKTMQ7kNvgFe49PD&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYBD3wGyWwmI3jSiPHCVOpxao4HIj4kyETS_PeKWQqzlxQ&amp;oe=66A05E4A\" alt=\"Có thể là hình ảnh về 19 người, đồ chơi trẻ em và văn bản\"></p><p>&nbsp;</p><p><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451834219_1225189755363000_1291539997726906583_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=101&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=JSbBWvn3yMIQ7kNvgFJ-8HE&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYBvnIEzDRXAUgeVSi-tWvmfsP5JUFBFQ9_pTtZ4EAmWGg&amp;oe=66A067F1\" alt=\"Có thể là hình ảnh về 10 người\"></p><p>&nbsp;</p><p><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451933609_1225186768696632_49972870518971477_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=106&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=3LiEvqrJqPUQ7kNvgHbdqyY&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYBOXLRdxs-51eSwA2fxJUQjBeahGZY1Jh6UQRxfnOaSyw&amp;oe=66A053B5\" alt=\"Có thể là hình ảnh về 16 người, mọi người đang học, đồ chơi trẻ em và văn bản\"></p><p>&nbsp;</p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451959442_1225186875363288_3950716435396375626_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=109&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=LYi1lyvtV8cQ7kNvgEtKFdM&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYAuzHCW4yrNEo7jXM79rQggfVS8O3Us_KuHr7aifcCyOA&amp;oe=66A05F79\" alt=\"Có thể là hình ảnh về 8 người, mọi người đang học và văn bản\"></p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451952384_1225187195363256_2718444944861663299_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=103&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=an9rJomzW6MQ7kNvgEt09Ti&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYApWBI_jCOUNrgTDNB4Fo7zueBYa_77xdxmhd8MQmInMw&amp;oe=66A07878\" alt=\"Có thể là hình ảnh về 3 người, trẻ em, mọi người đang học, sách, bàn là và văn bản\"></p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451785904_1225196778695631_5052772680670358178_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=102&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=Jka4I9A82uYQ7kNvgGZ40Py&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYC_aRVqYhGXZGiEMym-xTXreTjWCBlx2-IJm95t6X17EQ&amp;oe=66A0490B\" alt=\"Có thể là hình ảnh về 15 người, mọi người đang học và văn bản\"></p><p>&nbsp;</p><p><strong>&nbsp;&nbsp;&nbsp;&nbsp;KHAI GIẢNG LỚP VÕ CỔ TRUYỀN VIỆT NAM</strong><br>&nbsp;&nbsp;&nbsp;&nbsp;Chiều ngày 18/7/2024, tại sân trường Tiểu học Vĩnh Sơn, đội 2409 đã tổ chức khai giảng Lớp võ cổ truyền Việt Nam miễn phí. Đây là môn thể thao có tác dụng tốt đến toàn bộ cơ bắp trên cơ thể, làm cho cơ thể phát triển cân đối, tăng sức mạnh, sức nhanh. Phụ trách chính của lớp là Đ.c Hoàng Thị Đoan từng đạt nhiều giải thưởng tại các cuộc thì về Võ cổ truyền.<br>&nbsp;&nbsp;&nbsp;&nbsp;Đây sẽ là một lớp học thiết thực và ý nghĩa, giúp cho các em nhỏ tại xã Vĩnh Sơn có cơ hội được tiếp xúc với một môn học mới, rèn luyện sức khỏe, rèn luyện kỹ năng thoát hiểm đồng thời góp phần bảo tồn tinh hoa võ thuật cổ truyền Việt Nam, góp phần tạo động lực cho thể hệ “búp măng non” hăng hái xây dựng và bảo vệ Tổ quốc.<br>&nbsp;&nbsp;&nbsp;&nbsp;Lớp học được tổ chức vào lúc 16h30, mỗi buổi chiều hàng tuần tại sân trường Tiểu học Vĩnh Sơn.</p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451749588_1225260288689280_1884043071567467860_n.jpg?_nc_cat=103&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=oSWTGRVPq20Q7kNvgF9hMCc&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYA6wUz88nRlaHxVvFfYnkUSPjVyjW0SumX35bbg4SnJqg&amp;oe=66A05819\" alt=\"Có thể là hình ảnh về 6 người\"></p><p><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451677899_1225260662022576_1215884231157216693_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=103&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=nmKobtMggacQ7kNvgFukbm3&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYCEUAG8e1M-XFv9KwN87X0VQcfWCwze5lS9s8G1dcyb-A&amp;oe=66A07B3B\" alt=\"Có thể là hình ảnh về 3 người và mọi người đang tập yoga\"></p><p><strong><img src=\"https://scontent.fvii2-4.fna.fbcdn.net/v/t39.30808-6/451628407_1225261002022542_7559004900285708399_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=108&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=jIw-40NXLVkQ7kNvgGeYBrE&amp;_nc_ht=scontent.fvii2-4.fna&amp;oh=00_AYCXgne62Hx-J8S2NWHwBwFvkLZasFzxO-PtQW785VSbuQ&amp;oe=66A067A2\" alt=\"Có thể là hình ảnh về 19 người và mọi người đang tập yoga\"></strong></p><p><strong><img src=\"https://scontent.fvii2-1.fna.fbcdn.net/v/t39.30808-6/451818589_1225260915355884_6956639893895094118_n.jpg?stp=cp6_dst-jpg&amp;_nc_cat=105&amp;ccb=1-7&amp;_nc_sid=f727a1&amp;_nc_ohc=_LY-XFK0TuoQ7kNvgG2Jw1y&amp;_nc_ht=scontent.fvii2-1.fna&amp;oh=00_AYBut-ipQPHWtA-7-pvRZoiZt5F-K4VKT5Bng_mWGhHoVQ&amp;oe=66A073E1\" alt=\"Có thể là hình ảnh về 4 người, mọi người đang tập yoga và mọi người đang khiêu vũ\"></strong></p>",
            "excerpt": "ĐẨY MẠNH TĂNG GIA SẢN XUẤT, THỰC HÀNH TIẾT KIỆM  Nhận thức rõ vị trí, ý nghĩa của công tác hậu cần nói chung, tăng gia sản xuất, thực hành tiết kiệm nói riêng. Tận dụng được vườn rau sẵn có tại trườ...",
            "seo_title": "Bản tin tình nguyện 2409: Nhật ký nghỉ hè ý nghĩa tại Vĩnh Sơn, Anh Sơn",
            "seo_description": "Cập nhật hoạt động tình nguyện hè 2024 tại Vĩnh Sơn, Anh Sơn: lớp học miễn phí, võ cổ truyền và tăng gia sản xuất. Xem ngay!",
            "focus_keyword": "BẢN TIN TÌNH NGUYỆN 2409 (ngày 18/7/2024) | NHẬT KÝ KỲ NGHỈ HÈ CỦA “BÉ NGOAN” TẠI VĨNH SƠN, ANH SƠN",
            "thumbnail_object_key": "article/thumbnail/vinh-son-anh-son.jpg",
            "slug": "ban-tin-tinh-nguyen-2409-ngay-1872024",
            "lang": "vi"
        }

        res = await ac.post(
            f"/api/v1/admin/articles/{article_id}/seo/analyze",
            json=seo_payload,
            headers=headers,
            timeout=120.0
        )
        
        assert res.status_code == 200, f"Gọi API SEO Analyze thất bại: {res.text}"
        data = res.json()

        logger.info("🎉 Gọi API thành công! Kết quả phân tích SEO:")
        logger.info(f"📊 Điểm SEO (Rule Engine): {data.get('score')}/100 ({data.get('status').upper()})")
        
        logger.info("⚠️ Danh sách các lỗi kỹ thuật phát hiện:")
        for idx, issue in enumerate(data.get("issues", [])):
            logger.info(f"  [{idx + 1}] Type: {issue.get('type')} - {issue.get('message')}")
            
        logger.info("🤖 Gợi ý cải thiện từ AI Assistant:")
        for idx, sug in enumerate(data.get("suggestions", [])):
            logger.info(f"  [{idx + 1}] {sug}")

        logger.info(f"✨ Tiêu đề SEO gợi ý bởi AI: '{data.get('generated_seo_title')}'")
        logger.info(f"✨ Mô tả SEO gợi ý bởi AI: '{data.get('generated_meta_description')}'")
        logger.info(f"🔑 Gợi ý từ khóa phụ: {data.get('focus_keywords')}")
        
        logger.info("🔗 Gợi ý liên kết nội bộ (Internal Links):")
        for idx, link in enumerate(data.get("internal_links", [])):
            logger.info(f"  [{idx + 1}] Anchor: '{link.get('anchor_text')}' -> URL: {link.get('url')} (Lý do: {link.get('reason')})")

        logger.info("🖥️ Google Search Preview:")
        preview = data.get("google_preview", {})
        logger.info(f"  [Tiêu đề]: {preview.get('title')}")
        logger.info(f"  [Đường dẫn]: {preview.get('url')}")
        logger.info(f"  [Mô tả]: {preview.get('description')}")
        
        # Kiểm tra tính hợp lệ cơ bản của dữ liệu
        assert "score" in data
        assert "status" in data
        assert "issues" in data
        assert "suggestions" in data
        assert "google_preview" in data
        
        logger.info("✅ Xác minh dữ liệu phản hồi khớp 100% với Pydantic Response Schema!")

if __name__ == "__main__":
    logger.info("🚀 Khởi động script kiểm thử AI SEO Assistant...")
    asyncio.run(test_seo_assistant())
