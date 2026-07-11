import asyncio
import httpx
import json
import uuid

async def test_live_seo():
    print("=== LIVE DEPARTMENT SEO ANALYSIS TEST ===")
    
    # 1. Đăng nhập tài khoản Admin lấy Token
    login_payload = {
        "username": "superadmin",
        "password": "Password@123"
    }
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as ac:
        try:
            login_res = await ac.post("/api/v1/auth/login", json=login_payload)
            if login_res.status_code != 200:
                print(f"Không thể đăng nhập. Mã lỗi: {login_res.status_code}, Body: {login_res.text}")
                return
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("Đăng nhập thành công, đã nhận Admin Token!")
            
            # 2. Lấy danh sách departments để tìm một ID thực tế
            depts_res = await ac.get("/api/v1/portal/departments?lang=vi")
            if depts_res.status_code == 200 and depts_res.json():
                dept_id = depts_res.json()[0]["id"]
                print(f"Sử dụng Department ID thực tế: {dept_id}")
            else:
                dept_id = str(uuid.uuid4())
                print(f"Sử dụng Department ID tạm thời: {dept_id}")

            # 3. Gửi yêu cầu phân tích SEO cho khoa
            seo_payload = {
                "name": "Khoa Khoa học máy tính và Trí tuệ nhân tạo",
                "description": "Khoa đào tạo nguồn nhân lực chất lượng cao về Khoa học Máy tính, Trí tuệ Nhân tạo và Công nghệ phần mềm.",
                "mission": "<h3>Sứ mệnh khoa</h3><p>Đào tạo, nghiên cứu khoa học và chuyển giao công nghệ hàng đầu khu vực trong lĩnh vực Trí tuệ nhân tạo.</p>",
                "vision": "<h3>Tầm nhìn khoa</h3><p>Trở thành trung tâm đào tạo xuất sắc về Trí tuệ nhân tạo và Khoa học máy tính đạt chuẩn kiểm định quốc tế.</p>",
                "history": "<h3>Lịch sử phát triển</h3><p>Khoa có truyền thống hơn 20 năm xây dựng và phát triển, tiền thân từ tổ bộ môn tin học...</p>",
                "research_overview": "<h3>Hướng nghiên cứu chính</h3><p>Tập trung nghiên cứu Học máy, Xử lý ngôn ngữ tự nhiên và Thị giác máy tính.</p>",
                "seo_title": "Khoa KHMT & TTNT | Trường Đại học KTCN",
                "seo_description": "Trang giới thiệu chính thức Khoa Khoa học máy tính và Trí tuệ nhân tạo.",
                "focus_keyword": "Trí tuệ nhân tạo",
                "thumbnail_object_key": "dept/thumb.png",
                "logo_object_key": "dept/logo.png",
                "banner_object_key": "dept/banner.png",
                "slug": "khoa-khoa-hoc-may-tinh-va-tri-tue-nhan-tao",
                "lang": "vi"
            }
            
            res_seo = await ac.post(f"/api/v1/admin/departments/{dept_id}/seo/analyze", json=seo_payload, headers=headers, timeout=60.0)
            print(f"\nStatus Code: {res_seo.status_code}")
            if res_seo.status_code == 200:
                print("Response JSON:")
                print(json.dumps(res_seo.json(), indent=2, ensure_ascii=False))
            else:
                print(f"Lỗi: {res_seo.text}")
                
        except Exception as e:
            import traceback
            print(f"Lỗi khi thực hiện kiểm tra: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_seo())
