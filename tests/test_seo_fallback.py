import pytest
from app.shared.seo.helper import resolve_seo, strip_html_tags


def test_strip_html_tags():
    """Kiểm tra việc loại bỏ thẻ HTML."""
    html_text = "<p>Chào mừng bạn đến với <strong>Trường Đại học Vinh</strong>!</p>"
    clean = strip_html_tags(html_text)
    assert clean == "Chào mừng bạn đến với Trường Đại học Vinh !"

    assert strip_html_tags(None) == ""
    assert strip_html_tags("") == ""


def test_seo_fallback_all_null():
    """Tất cả trường SEO rỗng -> tự động fallback."""
    seo = resolve_seo(
        title="Đào tạo Công nghệ thông tin",
        description=None,
        content=None,
        tags=None,
        thumbnail_url=None,
        slug="dao-tao-cntt"
    )

    # 1. Title tự sinh ghép hậu tố trường
    assert seo.seo_title == "Đào tạo Công nghệ thông tin | Trường Kỹ thuật và Công nghệ - Đại học Vinh"
    
    # 2. Description tự sinh theo mặc định
    assert seo.seo_description == "Trang thông tin chính thức của Trường Kỹ thuật và Công nghệ - Đại học Vinh."

    # 3. Keywords tự sinh chứa default keywords
    assert "Đào tạo Công nghệ thông tin" in seo.seo_keywords
    assert "Trường Kỹ thuật và Công nghệ" in seo.seo_keywords

    # 4. Canonical tự sinh theo slug
    assert seo.seo_canonical == "https://kcnt.vinhuni.edu.vn/dao-tao-cntt"

    # 5. Robots mặc định
    assert seo.seo_robots == "index, follow"

    # 6. OG Image mặc định
    assert seo.seo_og_image_url == "https://kcnt.vinhuni.edu.vn/assets/images/default-banner.jpg"


def test_seo_fallback_custom_title():
    """Chỉ custom seo_title -> title lấy custom, các trường khác tự sinh."""
    seo = resolve_seo(
        title="Tin tức",
        description="Mô tả danh mục tin tức",
        custom_seo_title="Chuyên trang Tin Tức khoa CNTT"
    )

    assert seo.seo_title == "Chuyên trang Tin Tức khoa CNTT"
    assert seo.seo_description == "Mô tả danh mục tin tức"
    assert "Tin tức" in seo.seo_keywords


def test_seo_fallback_html_stripping():
    """Tự sinh Desc từ content có chứa HTML -> loại bỏ tags trước khi cắt."""
    html_content = "<div class='content'><p>Học viện Công nghệ Vinh đào tạo các ngành Kỹ thuật điện, CNTT, Cơ khí chế tạo...</p><span>Đọc thêm chi tiết tại đây</span></div>"
    seo = resolve_seo(
        title="Tuyển sinh",
        content=html_content
    )

    assert "<p>" not in seo.seo_description
    assert "Cơ khí chế tạo" in seo.seo_description
    assert seo.seo_description.endswith("...") or len(seo.seo_description) <= 160


def test_seo_fallback_og_image_priority():
    """Kiểm tra độ ưu tiên của ảnh OG Image (SEO Image -> Thumbnail -> Default)."""
    
    # Lớp 1: Có ảnh SEO
    seo_1 = resolve_seo(
        title="Test",
        thumbnail_url="http://media.com/thumb.jpg",
        custom_seo_og_image_url="http://media.com/seo-image.jpg"
    )
    assert seo_1.seo_og_image_url == "http://media.com/seo-image.jpg"

    # Lớp 2: Không có ảnh SEO, có ảnh đại diện (Thumbnail)
    seo_2 = resolve_seo(
        title="Test",
        thumbnail_url="http://media.com/thumb.jpg",
        custom_seo_og_image_url=None
    )
    assert seo_2.seo_og_image_url == "http://media.com/thumb.jpg"

    # Lớp 3: Không có ảnh nào -> Banner mặc định
    seo_3 = resolve_seo(
        title="Test",
        thumbnail_url=None,
        custom_seo_og_image_url=None
    )
    assert seo_3.seo_og_image_url == "https://kcnt.vinhuni.edu.vn/assets/images/default-banner.jpg"


def test_seo_fallback_canonical_slug():
    """Kiểm tra canonical url tự sinh."""
    seo_1 = resolve_seo(
        title="Test",
        slug="gioi-thieu/khoa-cntt"
    )
    assert seo_1.seo_canonical == "https://kcnt.vinhuni.edu.vn/gioi-thieu/khoa-cntt"

    seo_2 = resolve_seo(
        title="Test",
        slug=None,
        custom_seo_canonical="https://google.com"
    )
    assert seo_2.seo_canonical == "https://google.com"
