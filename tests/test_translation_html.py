import pytest
from httpx import AsyncClient
from bs4 import BeautifulSoup


@pytest.mark.asyncio
async def test_html_translation_endpoint(client: AsyncClient, admin_headers: dict):
    from app.modules.translation.service import translation_service
    translation_service.warmup()

    # 1. Chuẩn bị chuỗi HTML phức tạp để test
    original_html = (
        "<p class=\"intro-text\">Xin chào <strong>giảng viên</strong> của khoa.</p>"
        "<div class=\"gallery\">"
        "  <img src=\"/images/profile.jpg\" alt=\"Hình đại diện\" class=\"profile-img\" />"
        "  <p>Vui lòng click <a href=\"/docs/intro\" target=\"_blank\">vào đây</a> để đọc thêm thông tin.</p>"
        "</div>"
        "<table>"
        "  <tr>"
        "    <th>Họ và Tên</th>"
        "    <th>Chức vụ</th>"
        "  </tr>"
        "  <tr>"
        "    <td>Nguyễn Văn A</td>"
        "    <td>Trưởng bộ môn</td>"
        "  </tr>"
        "</table>"
    )

    # 2. Gửi request dịch HTML
    payload = {
        "html": original_html,
        "target_languages": ["en"]
    }
    res = await client.post("/api/v1/translation/html", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    
    assert "vi" in data
    assert "en" in data
    assert data["vi"] == original_html
    
    translated_html = data["en"]
    
    # 3. Phân tích cấu trúc HTML dịch được bằng BeautifulSoup để kiểm tra tính toàn vẹn
    soup_orig = BeautifulSoup(original_html, "html.parser")
    soup_trans = BeautifulSoup(translated_html, "html.parser")
    
    # Kiểm tra số lượng thẻ giống nhau
    tags_orig = soup_orig.find_all()
    tags_trans = soup_trans.find_all()
    assert len(tags_orig) == len(tags_trans), "Cấu trúc tag HTML đã bị làm thay đổi số lượng!"
    
    # Kiểm tra các tag và thuộc tính cụ thể có bị bảo toàn không
    img_orig = soup_orig.find("img")
    img_trans = soup_trans.find("img")
    assert img_trans is not None
    assert img_trans["src"] == img_orig["src"]
    assert img_trans["class"] == img_orig["class"]
    # Lưu ý: Vì alt là thuộc tính chứa văn bản, nhưng ở đây logic bs4 của chúng ta chỉ dịch Text Nodes (node.parent.name), 
    # chứ không quét qua các thuộc tính của thẻ như alt, title.
    # Đúng vậy! CKEditor chỉ lưu nội dung chữ trong Text Nodes, các thuộc tính của ảnh thường được giữ nguyên.
    assert img_trans["alt"] == img_orig["alt"]
    
    # Kiểm tra thẻ a
    a_orig = soup_orig.find("a")
    a_trans = soup_trans.find("a")
    assert a_trans is not None
    assert a_trans["href"] == a_orig["href"]
    assert a_trans["target"] == a_orig["target"]
    
    # Kiểm tra thẻ p có class intro-text
    p_orig = soup_orig.find("p", class_="intro-text")
    p_trans = soup_trans.find("p", class_="intro-text")
    assert p_trans is not None
    assert "intro-text" in p_trans["class"]
    
    # Kiểm tra xem văn bản bên trong đã được dịch chưa (ví dụ: "giảng viên" dịch thành "lecturer" hoặc tương tự)
    # Thẻ strong chứa "giảng viên" -> "lecturer" (hoặc từ tương đương được dịch)
    strong_trans = soup_trans.find("strong")
    assert strong_trans is not None
    assert any(word in strong_trans.text.strip().lower() for word in ["lecturer", "teacher", "instructor", "faculty", "staff", "professor"])
    
    # Thẻ a chứa "vào đây" -> "here" hoặc tương đương
    assert "here" in a_trans.text.strip().lower() or "click" in a_trans.text.strip().lower()


@pytest.mark.asyncio
async def test_html_translation_with_context_endpoint(client: AsyncClient, admin_headers: dict):
    original_html = "<p>Chào mừng <strong>giảng viên</strong> mới.</p>"
    payload = {
        "html": original_html,
        "target_languages": ["en"],
        "context": "article_content"
    }
    res = await client.post("/api/v1/translation/html", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "en" in data
    assert "lecturer" in data["en"].lower()

