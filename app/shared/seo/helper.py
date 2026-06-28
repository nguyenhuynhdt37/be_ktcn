import re
from typing import Optional, List
from pydantic import BaseModel


class ResolvedSEO(BaseModel):
    """Cấu trúc dữ liệu SEO cuối cùng sau khi đã xử lý Fallback 3 lớp."""
    seo_title: str
    seo_description: str
    seo_keywords: str
    seo_canonical: str
    seo_robots: str
    seo_og_image_url: str


def strip_html_tags(html_text: Optional[str]) -> str:
    """Loại bỏ các thẻ HTML để lấy văn bản thuần túy."""
    if not html_text:
        return ""
    # Thay thế các thẻ HTML bằng khoảng trắng
    clean_text = re.sub(r"<[^>]*>", " ", html_text)
    # Loại bỏ khoảng trắng thừa
    clean_text = re.sub(r"\s+", " ", clean_text)
    return clean_text.strip()


def resolve_seo(
    title: str,
    description: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    thumbnail_url: Optional[str] = None,
    slug: Optional[str] = None,
    custom_seo_title: Optional[str] = None,
    custom_seo_description: Optional[str] = None,
    custom_seo_keywords: Optional[str] = None,
    custom_seo_canonical: Optional[str] = None,
    custom_seo_robots: Optional[str] = None,
    custom_seo_og_image_url: Optional[str] = None,
    base_domain: str = "https://kcnt.vinhuni.edu.vn",
    default_og_image: str = "https://kcnt.vinhuni.edu.vn/assets/images/default-banner.jpg",
) -> ResolvedSEO:
    """
    Áp dụng quy tắc ưu tiên 3 lớp (Manual -> AI/Auto -> Website Default) để resolve dữ liệu SEO.
    """
    # ─── 1. SEO TITLE ───
    if custom_seo_title and custom_seo_title.strip():
        resolved_title = custom_seo_title.strip()
    else:
        resolved_title = f"{title.strip()} | Trường Kỹ thuật và Công nghệ - Đại học Vinh"

    # ─── 2. SEO DESCRIPTION ───
    if custom_seo_description and custom_seo_description.strip():
        resolved_desc = custom_seo_description.strip()
    else:
        # Tự động sinh:
        # a. Ưu tiên excerpt/summary (được truyền qua tham số description)
        if description and description.strip():
            clean_desc = strip_html_tags(description)
            resolved_desc = clean_desc[:155] + "..." if len(clean_desc) > 155 else clean_desc
        # b. Cắt 150-160 ký tự đầu tiên của content (sau khi bỏ HTML)
        elif content and content.strip():
            clean_content = strip_html_tags(content)
            resolved_desc = clean_content[:155] + "..." if len(clean_content) > 155 else clean_content
        # c. Sử dụng mô tả mặc định của website
        else:
            resolved_desc = "Trang thông tin chính thức của Trường Kỹ thuật và Công nghệ - Đại học Vinh."

    # ─── 3. SEO KEYWORDS ───
    if custom_seo_keywords and custom_seo_keywords.strip():
        resolved_keywords = custom_seo_keywords.strip()
    else:
        # Tự động sinh: Tên bài viết/danh mục + tags + từ khóa mặc định
        default_keywords = [
            "Trường Kỹ thuật và Công nghệ",
            "Đại học Vinh",
            "Vinh University",
            "Tuyển sinh",
            "Đào tạo",
            "Nghiên cứu khoa học"
        ]
        keyword_parts = []
        if title:
            keyword_parts.append(title.strip())
        if tags:
            keyword_parts.extend([t.strip() for t in tags if t.strip()])
            
        # Ghép các phần lại với nhau
        all_keywords = keyword_parts + default_keywords
        # Loại bỏ trùng lặp giữ nguyên thứ tự
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw)
                
        resolved_keywords = ", ".join(unique_keywords)

    # ─── 4. CANONICAL URL ───
    if custom_seo_canonical and custom_seo_canonical.strip():
        resolved_canonical = custom_seo_canonical.strip()
    else:
        # Tự sinh theo slug chuẩn của hệ thống
        if slug:
            resolved_canonical = f"{base_domain.rstrip('/')}/{slug.strip('/')}"
        else:
            resolved_canonical = base_domain

    # ─── 5. ROBOTS ───
    if custom_seo_robots and custom_seo_robots.strip():
        resolved_robots = custom_seo_robots.strip()
    else:
        resolved_robots = "index, follow"

    # ─── 6. OPEN GRAPH IMAGE ───
    if custom_seo_og_image_url and custom_seo_og_image_url.strip():
        resolved_og_image = custom_seo_og_image_url.strip()
    elif thumbnail_url and thumbnail_url.strip():
        resolved_og_image = thumbnail_url.strip()
    else:
        resolved_og_image = default_og_image

    return ResolvedSEO(
        seo_title=resolved_title,
        seo_description=resolved_desc,
        seo_keywords=resolved_keywords,
        seo_canonical=resolved_canonical,
        seo_robots=resolved_robots,
        seo_og_image_url=resolved_og_image,
    )
