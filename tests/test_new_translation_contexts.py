import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_new_translation_contexts(client: AsyncClient, admin_headers: dict):
    # Test translating with department_mission context
    payload_mission = {
        "text": "Sứ mệnh của chúng tôi là đào tạo nguồn nhân lực chất lượng cao trong lĩnh vực kỹ thuật và công nghệ.",
        "target_languages": ["en"],
        "context": "department_mission"
    }
    res_mission = await client.post("/api/v1/translation", json=payload_mission, headers=admin_headers)
    assert res_mission.status_code == 200
    data_mission = res_mission.json()
    assert data_mission["vi"] == payload_mission["text"]
    assert "en" in data_mission
    print("\nMission Translation Output:")
    print(data_mission["en"])

    # Test translating with department_vision context
    payload_vision = {
        "text": "Trở thành khoa hàng đầu về nghiên cứu khoa học và đổi mới sáng tạo trong nước và quốc tế.",
        "target_languages": ["en"],
        "context": "department_vision"
    }
    res_vision = await client.post("/api/v1/translation", json=payload_vision, headers=admin_headers)
    assert res_vision.status_code == 200
    data_vision = res_vision.json()
    assert data_vision["vi"] == payload_vision["text"]
    assert "en" in data_vision
    print("\nVision Translation Output:")
    print(data_vision["en"])

    # Test HTML translation with department_history context
    payload_history = {
        "html": "<p>Khoa được thành lập vào năm 2002 theo quyết định của Hiệu trưởng.</p>",
        "target_languages": ["en"],
        "context": "department_history"
    }
    res_history = await client.post("/api/v1/translation/html", json=payload_history, headers=admin_headers)
    assert res_history.status_code == 200
    data_history = res_history.json()
    assert "en" in data_history
    assert "<p>" in data_history["en"]
    print("\nHistory Translation HTML Output:")
    print(data_history["en"])
