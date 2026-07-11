import asyncio
import httpx
import json

async def test_live_translation():
    print("=== LIVE TRANSLATION TEST WITH NEW DEPT CONTEXTS ===")
    
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
            
            # 2. Test dịch với context: department_mission
            payload_mission = {
                "text": "Sứ mệnh của chúng tôi là đào tạo nguồn nhân lực chất lượng cao trong lĩnh vực kỹ thuật và công nghệ.",
                "target_languages": ["en"],
                "context": "department_mission"
            }
            res_mission = await ac.post("/api/v1/translation", json=payload_mission, headers=headers)
            print(f"\n[POST /api/v1/translation] - context: department_mission")
            print(f"Status Code: {res_mission.status_code}")
            print(json.dumps(res_mission.json(), indent=2, ensure_ascii=False))
            
            # 3. Test dịch với context: department_vision
            payload_vision = {
                "text": "Trở thành khoa hàng đầu về nghiên cứu khoa học và đổi mới sáng tạo trong nước và quốc tế.",
                "target_languages": ["en"],
                "context": "department_vision"
            }
            res_vision = await ac.post("/api/v1/translation", json=payload_vision, headers=headers)
            print(f"\n[POST /api/v1/translation] - context: department_vision")
            print(f"Status Code: {res_vision.status_code}")
            print(json.dumps(res_vision.json(), indent=2, ensure_ascii=False))

            # 4. Test dịch HTML với context: department_history
            payload_history = {
                "html": "<h3>Lịch sử hình thành</h3><p>Khoa được thành lập vào năm 2002 theo quyết định của Hiệu trưởng.</p>",
                "target_languages": ["en"],
                "context": "department_history"
            }
            res_history = await ac.post("/api/v1/translation/html", json=payload_history, headers=headers)
            print(f"\n[POST /api/v1/translation/html] - context: department_history")
            print(f"Status Code: {res_history.status_code}")
            print(json.dumps(res_history.json(), indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"Lỗi khi thực hiện kiểm tra: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_translation())
