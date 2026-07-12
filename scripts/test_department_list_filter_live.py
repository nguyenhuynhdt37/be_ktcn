import asyncio
import httpx
import json

async def test_live_filter():
    print("=== LIVE DEPARTMENT LIST FILTER BY UNIT_TYPE TEST ===")
    
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
            
            # 2. Thử lọc với unit_type=department
            res_dept = await ac.get("/api/v1/admin/departments?unit_type=department&page=1&page_size=3", headers=headers)
            print(f"\n[GET /api/v1/admin/departments?unit_type=department] - Status: {res_dept.status_code}")
            dept_items = res_dept.json().get("items", [])
            print(f"Số lượng khoa tìm thấy: {len(dept_items)}")
            for item in dept_items:
                print(f"  - ID: {item['id']} | Name: {item['name']} | Unit Type: {item['unit_type']}")
                
            # 3. Thử lọc với unit_type=office
            res_office = await ac.get("/api/v1/admin/departments?unit_type=office&page=1&page_size=3", headers=headers)
            print(f"\n[GET /api/v1/admin/departments?unit_type=office] - Status: {res_office.status_code}")
            office_items = res_office.json().get("items", [])
            print(f"Số lượng phòng ban tìm thấy: {len(office_items)}")
            for item in office_items:
                print(f"  - ID: {item['id']} | Name: {item['name']} | Unit Type: {item['unit_type']}")
                
        except Exception as e:
            print(f"Lỗi khi thực hiện kiểm tra: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_filter())
