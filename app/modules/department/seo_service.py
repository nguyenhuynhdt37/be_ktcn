import re
import json
import uuid
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Comment
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.department.models import Department, DepartmentTranslation
from app.modules.language.models import Language
from app.modules.category.models import Category, CategoryTranslation
from app.modules.tag.models import Tag, TagTranslation
from app.modules.staff.models import Staff
from app.modules.article.schemas.admin import (
    SEOElementIssue,
    SEOElementAnalysis,
    SEOAuditDetails,
    InternalLinkSuggestion,
    GooglePreviewInfo,
    ArticleSEOAnalyzeResponse,
)
from app.modules.department.schemas.admin import DepartmentSEOAnalyzeRequest
from app.shared.ai import get_ai_service
from app.modules.article.service import slugify


class DepartmentSEOService:
    """
    Service độc lập quản lý logic phân tích SEO cho Khoa/Bộ môn (Department SEO Assistant).
    Chấm điểm tĩnh bằng Rule Engine và gọi AI Hub (Gemini) để sinh gợi ý tối ưu.
    """

    def _preprocess_content(self, html_fields: List[str]) -> Dict[str, Any]:
        """
        Tiền xử lý và gộp các trường HTML (mission, vision, history, research_overview)
        để phân tích cấu trúc SEO và trích xuất text thuần.
        """
        headings = []
        paragraphs = []
        images_info = []
        clean_text_parts = []

        for html_content in html_fields:
            if not html_content:
                continue

            soup = BeautifulSoup(html_content, "html.parser")

            # 1. Loại bỏ comment
            for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            # 2. Loại bỏ script và style
            for tag in soup(["script", "style"]):
                tag.extract()

            # 3. Loại bỏ Base64 Image
            for img in soup.find_all("img"):
                src = img.get("src", "")
                alt = img.get("alt", "")
                is_base64 = False
                if src.startswith("data:"):
                    is_base64 = True
                    img["src"] = ""
                images_info.append({"alt": alt, "src_is_base64": is_base64})

            # 4. Loại bỏ các thuộc tính trình diễn / CSS
            for tag in soup.find_all(True):
                attrs_to_del = [
                    attr for attr in tag.attrs 
                    if attr in ["class", "style", "id", "onclick"] or attr.startswith("data-")
                ]
                for attr in attrs_to_del:
                    del tag[attr]

            # 5. Trích xuất cấu trúc ngữ nghĩa
            for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                headings.append(f"{h.name.upper()}: {h.get_text().strip()}")

            for p in soup.find_all("p"):
                text = p.get_text().strip()
                if text:
                    paragraphs.append(text)

            clean_text_parts.append(soup.get_text())

        clean_text = " ".join(clean_text_parts)
        # Chuẩn hóa khoảng trắng
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return {
            "headings": headings,
            "paragraphs": paragraphs,
            "images": images_info,
            "clean_text": clean_text,
        }

    def _run_rule_engine(
        self,
        name: str,
        description: str,
        seo_title: str,
        seo_description: str,
        slug: str,
        thumbnail_object_key: Optional[str],
        logo_object_key: Optional[str],
        banner_object_key: Optional[str],
        preprocessed: Dict[str, Any],
        focus_keyword: Optional[str]
    ) -> Dict[str, Any]:
        """
        Rule Engine chấm điểm tĩnh (tối đa 100 điểm) và phát hiện các vấn đề kỹ thuật cơ bản của khoa/bộ môn.
        """
        issues: List[SEOElementIssue] = []
        title_issues: List[SEOElementIssue] = []
        meta_issues: List[SEOElementIssue] = []
        content_issues: List[SEOElementIssue] = []
        link_issues: List[SEOElementIssue] = []

        # --- 1. TITLE ANALYSIS (Tối đa 15 điểm) ---
        title_score = 15
        eval_title = seo_title or name
        if not eval_title:
            title_score = 0
            title_issues.append(SEOElementIssue(type="missing_title", message="Thiếu tên khoa/bộ môn hoặc tiêu đề SEO."))
        else:
            title_len = len(eval_title)
            if title_len < 40:
                title_score = 10
                title_issues.append(SEOElementIssue(
                    type="title_too_short", 
                    message=f"Tiêu đề SEO quá ngắn ({title_len} ký tự). Độ dài tối ưu là 40 - 65 ký tự để tránh hiển thị kém trên Google."
                ))
            elif title_len > 65:
                title_score = 10
                title_issues.append(SEOElementIssue(
                    type="title_too_long", 
                    message=f"Tiêu đề SEO quá dài ({title_len} ký tự). Độ dài tối ưu là 40 - 65 ký tự để tránh bị cắt bớt trên Google."
                ))
            
            if focus_keyword:
                if focus_keyword.lower() not in eval_title.lower():
                    title_score = max(0, title_score - 5)
                    title_issues.append(SEOElementIssue(
                        type="title_missing_keyword", 
                        message=f"Tiêu đề SEO không chứa từ khóa chính '{focus_keyword}'."
                    ))

        # --- 2. META DESCRIPTION ANALYSIS (Tối đa 15 điểm) ---
        meta_score = 15
        eval_desc = seo_description or description
        if not eval_desc:
            meta_score = 0
            meta_issues.append(SEOElementIssue(type="missing_meta_description", message="Thiếu mô tả giới thiệu hoặc mô tả SEO."))
        else:
            desc_len = len(eval_desc)
            if desc_len < 110:
                meta_score = 10
                meta_issues.append(SEOElementIssue(
                    type="meta_too_short", 
                    message=f"Mô tả SEO quá ngắn ({desc_len} ký tự). Độ dài tối ưu là 110 - 160 ký tự để cung cấp đầy đủ thông tin."
                ))
            elif desc_len > 160:
                meta_score = 10
                meta_issues.append(SEOElementIssue(
                    type="meta_too_long", 
                    message=f"Mô tả SEO quá dài ({desc_len} ký tự). Độ dài tối ưu là 110 - 160 ký tự để không bị Google cắt ngắn."
                ))
            
            if focus_keyword:
                if focus_keyword.lower() not in eval_desc.lower():
                    meta_score = max(0, meta_score - 5)
                    meta_issues.append(SEOElementIssue(
                        type="meta_missing_keyword", 
                        message=f"Mô tả SEO không chứa từ khóa chính '{focus_keyword}'."
                    ))

        # --- 3. MEDIA & SLUG ANALYSIS (Tối đa 25 điểm) ---
        # Logo & Banner & Thumbnail (15đ)
        media_score = 15
        if not logo_object_key:
            media_score -= 5
            issues.append(SEOElementIssue(type="missing_logo", message="Khoa chưa có Logo đại diện."))
        if not banner_object_key:
            media_score -= 5
            issues.append(SEOElementIssue(type="missing_banner", message="Khoa chưa cấu hình Banner hero."))
        if not thumbnail_object_key:
            media_score -= 5
            issues.append(SEOElementIssue(type="missing_thumbnail", message="Khoa chưa có ảnh đại diện nhỏ (Thumbnail)."))
        
        # Slug (10đ)
        slug_score = 10
        if not slug:
            slug_score = 0
            issues.append(SEOElementIssue(type="missing_slug", message="Khoa/Bộ môn chưa cấu hình Slug."))
        else:
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
                slug_score = 5
                issues.append(SEOElementIssue(
                    type="invalid_slug", 
                    message="Slug không chuẩn URL. Chỉ được chứa chữ thường không dấu, số và dấu gạch ngang."
                ))

        # --- 4. CONTENT & HEADING ANALYSIS (Tối đa 30 điểm) ---
        content_score = 30
        clean_text = preprocessed.get("clean_text", "")
        word_count = len(clean_text.split())
        
        # Phân tích độ dài nội dung (15đ)
        if word_count == 0:
            content_score = 0
            content_issues.append(SEOElementIssue(type="empty_content", message="Nội dung trang khoa hoàn toàn trống."))
        elif word_count < 200:
            content_score -= 10
            content_issues.append(SEOElementIssue(
                type="content_too_short", 
                message=f"Nội dung trang khoa quá ngắn ({word_count} từ). Nên viết tối thiểu 200 - 300 từ giới thiệu đầy đủ sứ mệnh, lịch sử."
            ))

        # Phân tích Heading (15đ)
        headings = preprocessed.get("headings", [])
        h2_count = sum(1 for h in headings if h.startswith("H2:"))
        h1_in_content = sum(1 for h in headings if h.startswith("H1:"))
        
        heading_penalty = 0
        if h2_count == 0:
            heading_penalty += 10
            content_issues.append(SEOElementIssue(
                type="missing_h2", 
                message="Nội dung thiếu tiêu đề phụ H2. Hãy sử dụng các thẻ H2 để cấu trúc các mục Sứ mệnh, Tầm nhìn, Lịch sử."
            ))
        if h1_in_content > 0:
            heading_penalty += 5
            content_issues.append(SEOElementIssue(
                type="duplicate_h1", 
                message="Nội dung trang khoa chứa thẻ H1. Tránh sử dụng H1 trong nội dung giới thiệu chi tiết."
            ))
        content_score = max(0, content_score - heading_penalty)

        # --- 5. KEYWORD DENSITY ANALYSIS (Tối đa 15 điểm) ---
        keyword_score = 15
        keyword_density = 0.0
        if focus_keyword and word_count > 0:
            # Đếm số lần xuất hiện không phân biệt hoa thường
            kw_matches = len(re.findall(re.escape(focus_keyword.lower()), clean_text.lower()))
            keyword_density = (kw_matches / word_count) * 100
            
            if keyword_density == 0:
                keyword_score = 0
                content_issues.append(SEOElementIssue(
                    type="keyword_not_found", 
                    message=f"Từ khóa chính '{focus_keyword}' không xuất hiện trong bất kỳ phần giới thiệu/sứ mệnh nào."
                ))
            elif keyword_density < 0.5:
                keyword_score = 10
                content_issues.append(SEOElementIssue(
                    type="keyword_density_low", 
                    message=f"Mật độ từ khóa chính thấp ({keyword_density:.2f}%). Cân nhắc chèn tự nhiên từ khóa chính vào các đoạn mô tả."
                ))
            elif keyword_density > 3.0:
                keyword_score = 5
                content_issues.append(SEOElementIssue(
                    type="keyword_density_high", 
                    message=f"Mật độ từ khóa chính quá cao ({keyword_density:.2f}%). Tránh spam từ khóa quá nhiều để tránh bị Google phạt."
                ))

        # Tổng hợp điểm và vấn đề
        total_score = title_score + meta_score + media_score + slug_score + content_score + keyword_score
        all_issues = issues + title_issues + meta_issues + content_issues + link_issues

        # Phân loại trạng thái
        status = "good"
        if total_score < 50:
            status = "error"
        elif total_score < 80:
            status = "warning"

        title_analysis = SEOElementAnalysis(
            score=int(title_score * 100 / 15) if eval_title else 0,
            status="good" if title_score >= 15 else ("warning" if title_score >= 10 else "error"),
            message="Tiêu đề SEO tốt." if title_score >= 15 else "Tiêu đề SEO cần được tối ưu lại.",
            issues=title_issues
        )

        meta_analysis = SEOElementAnalysis(
            score=int(meta_score * 100 / 15) if eval_desc else 0,
            status="good" if meta_score >= 15 else ("warning" if meta_score >= 10 else "error"),
            message="Mô tả SEO tốt." if meta_score >= 15 else "Mô tả SEO cần được cải thiện.",
            issues=meta_issues
        )

        content_analysis = SEOElementAnalysis(
            score=int(content_score * 100 / 30) if word_count > 0 else 0,
            status="good" if content_score >= 25 else ("warning" if content_score >= 15 else "error"),
            message="Nội dung trang khoa được cấu trúc tốt." if content_score >= 25 else "Nội dung trang khoa cần cấu trúc và bổ sung thêm.",
            issues=content_issues
        )

        link_analysis = SEOElementAnalysis(
            score=100,
            status="good",
            message="Không có vấn đề liên kết kỹ thuật.",
            issues=link_issues
        )

        return {
            "score": total_score,
            "status": status,
            "issues": all_issues,
            "keyword_density": keyword_density,
            "details": SEOAuditDetails(
                title_analysis=title_analysis,
                meta_description_analysis=meta_analysis,
                content_analysis=content_analysis,
                link_analysis=link_analysis
            )
        }

    async def _get_internal_link_targets(self, db: AsyncSession, lang_code: str) -> List[Dict[str, str]]:
        """
        Truy vấn các thực thể liên quan (Categories, Tags, Departments, Staffs) làm link nội bộ.
        """
        targets = []
        try:
            lang_stmt = select(Language.id).where(Language.code == lang_code, Language.is_active == True)
            lang_res = await db.execute(lang_stmt)
            lang_id = lang_res.scalar_one_or_none()
            if not lang_id:
                lang_stmt = select(Language.id).where(Language.is_default == True)
                lang_res = await db.execute(lang_stmt)
                lang_id = lang_res.scalar_one_or_none()

            # 1. Categories
            if lang_id:
                cat_stmt = select(CategoryTranslation.name, CategoryTranslation.slug).where(
                    CategoryTranslation.language_id == lang_id
                ).limit(15)
                cat_res = await db.execute(cat_stmt)
                for name, slug in cat_res.all():
                    targets.append({
                        "name": name,
                        "url": f"/portal/categories/{slug}",
                        "type": "Danh mục bài viết"
                    })

            # 2. Departments (Khoa khác)
            if lang_id:
                dep_stmt = select(DepartmentTranslation.name, DepartmentTranslation.slug).where(
                    DepartmentTranslation.language_id == lang_id
                ).limit(15)
                dep_res = await db.execute(dep_stmt)
                for name, slug in dep_res.all():
                    targets.append({
                        "name": name,
                        "url": f"/portal/departments/{slug}",
                        "type": "Bộ môn / Khoa"
                    })

            # 3. Staffs (Giảng viên / Nhân sự)
            staff_stmt = select(Staff.full_name, Staff.slug).where(Staff.is_active == True).limit(15)
            staff_res = await db.execute(staff_stmt)
            for full_name, slug in staff_res.all():
                targets.append({
                    "name": full_name,
                    "url": f"/portal/staffs/{slug}",
                    "type": "Cán bộ / Giảng viên"
                })

        except Exception as e:
            logger.error(f"Error fetching internal link targets: {e}")
            targets = [
                {"name": "Trang chủ", "url": "/", "type": "Trang chính"},
                {"name": "Tuyển sinh", "url": "/portal/categories/tuyen-sinh", "type": "Danh mục"},
                {"name": "Đào tạo", "url": "/portal/categories/dao-tao", "type": "Danh mục"},
            ]
        
        return targets

    async def analyze_department_seo(
        self,
        db: AsyncSession,
        department_id: uuid.UUID,
        payload: DepartmentSEOAnalyzeRequest,
        current_user: Any,
    ) -> ArticleSEOAnalyzeResponse:
        """
        Thực hiện phân tích SEO cho Khoa/Bộ môn dựa trên Rule Engine và AI Hub gợi ý.
        """
        dept = None
        translation = None
        
        try:
            stmt = select(Department).where(Department.id == department_id)
            res = await db.execute(stmt)
            dept = res.scalar_one_or_none()
            
            if dept:
                lang_stmt = select(Language.id).where(Language.code == payload.lang)
                lang_res = await db.execute(lang_stmt)
                lang_id = lang_res.scalar_one_or_none()
                
                if lang_id:
                    trans_stmt = select(DepartmentTranslation).where(
                        DepartmentTranslation.department_id == department_id,
                        DepartmentTranslation.language_id == lang_id
                    )
                    trans_res = await db.execute(trans_stmt)
                    translation = trans_res.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"DB lookup failed for department {department_id}: {e}. Proceeding with payload only.")

        # Merge dữ liệu
        name = payload.name if payload.name is not None else (translation.name if translation else "")
        description = payload.description if payload.description is not None else (translation.description if translation else "")
        mission = payload.mission if payload.mission is not None else (translation.mission if translation else "")
        vision = payload.vision if payload.vision is not None else (translation.vision if translation else "")
        history = payload.history if payload.history is not None else (translation.history if translation else "")
        research_overview = payload.research_overview if payload.research_overview is not None else (translation.research_overview if translation else "")
        seo_title = payload.seo_title if payload.seo_title is not None else (translation.seo_title if translation else "")
        seo_description = payload.seo_description if payload.seo_description is not None else (translation.seo_description if translation else "")
        slug = payload.slug if payload.slug is not None else (translation.slug if translation else slugify(name))
        
        thumbnail_object_key = payload.thumbnail_object_key if payload.thumbnail_object_key is not None else (dept.thumbnail_object_key if dept else None)
        logo_object_key = payload.logo_object_key if payload.logo_object_key is not None else (dept.logo_object_key if dept else None)
        banner_object_key = payload.banner_object_key if payload.banner_object_key is not None else (dept.banner_object_key if dept else None)
        
        focus_keyword = payload.focus_keyword

        # Tiền xử lý nội dung
        rich_html_fields = [mission, vision, history, research_overview]
        preprocessed = self._preprocess_content(rich_html_fields)

        # Chạy Rule Engine
        rules_result = self._run_rule_engine(
            name=name,
            description=description,
            seo_title=seo_title,
            seo_description=seo_description,
            slug=slug,
            thumbnail_object_key=thumbnail_object_key,
            logo_object_key=logo_object_key,
            banner_object_key=banner_object_key,
            preprocessed=preprocessed,
            focus_keyword=focus_keyword
        )

        google_title = seo_title or name or "Tiêu đề trang khoa..."
        google_desc = seo_description or description or "Mô tả trang khoa hiển thị trên Google..."
        google_url = f"https://ktcn.edu.vn/portal/departments/{slug}" if slug else "https://ktcn.edu.vn/portal/departments/slug-khoa"
        google_preview = GooglePreviewInfo(
            title=google_title[:70] + "..." if len(google_title) > 70 else google_title,
            url=google_url,
            description=google_desc[:160] + "..." if len(google_desc) > 160 else google_desc
        )

        # Gợi ý link nội bộ
        internal_targets = await self._get_internal_link_targets(db, payload.lang)

        # Gọi AI Hub (Gemini)
        ai_service = get_ai_service()
        user_prompt = f"""
        Bạn là chuyên gia tối ưu hóa công cụ tìm kiếm (SEO Specialist) cho website trường Đại học.
        Hãy phân tích dữ liệu trang giới thiệu Khoa/Bộ môn học thuật đã được tiền xử lý dưới đây và đưa ra đánh giá, gợi ý cải thiện cụ thể.

        THÔNG TIN KHOA/BỘ MÔN:
        - Tên Khoa: {name}
        - Giới thiệu ngắn: {description}
        - Tiêu đề SEO hiện tại: {seo_title or '(Chưa có)'}
        - Mô tả SEO hiện tại: {seo_description or '(Chưa có)'}
        - Từ khóa chính muốn tập trung: {focus_keyword or '(Chưa nhập)'}

        CẤU TRÚC NỘI DUNG CHI TIẾT (ĐÃ TIỀN XỬ LÝ TỪ CÁC TRƯỜNG SỨ MỆNH, TẦM NHÌN, LỊCH SỬ, NGHIÊN CỨU):
        - Các Tiêu đề phụ (Headings): {json.dumps(preprocessed.get("headings", []), ensure_ascii=False)}
        - Tổng số từ: {len(preprocessed.get("clean_text", "").split())} từ.
        - Mật độ xuất hiện từ khóa chính thực tế: {rules_result.get("keyword_density"):.2f}%.

        KẾT QUẢ PHÂN TÍCH TĨNH:
        - Điểm SEO tính được: {rules_result.get("score")}/100.
        - Các lỗi phát hiện: {[issue.message for issue in rules_result.get("issues")]}

        DANH SÁCH THỰC THỂ KHẢ DỤNG ĐỂ GỢI Ý LIÊN KẾT NỘI BỘ (INTERNAL LINK):
        {json.dumps(internal_targets, ensure_ascii=False)}

        YÊU CẦU ĐỐI VỚI BẠN:
        Hãy trả về kết quả dạng JSON khớp chính xác với cấu trúc dưới đây để backend xử lý:
        {{
            "suggestions": [
                "Mảng chứa TỐI ĐA 4 gợi ý cải thiện, viết thật ngắn gọn, súc tích (dưới 15 từ mỗi gợi ý)."
            ],
            "generated_seo_title": "Tiêu đề SEO mới tối ưu hơn cho Khoa (dài 45-65 ký tự, chứa từ khóa chính, trang trọng)",
            "generated_meta_description": "Mô tả SEO mới tối ưu hơn cho Khoa (dài 120-160 ký tự, chứa từ khóa chính, hấp dẫn người học/đối tác)",
            "focus_keywords": [
                "Mảng chứa TỐI ĐA 2 từ khóa phụ/liên quan tiềm năng học thuật hoặc ngành học của Khoa."
            ],
            "internal_links": [
                {{
                    "anchor_text": "Cụm từ chính xác xuất hiện trong văn bản giới thiệu khoa mà bạn khuyên nên gắn link",
                    "url": "Đường dẫn URL tương ứng lấy từ danh sách thực thể được cung cấp",
                    "reason": "Lý do tại sao nên chèn liên kết nội bộ này"
                }}
            ]
        }}

        CHÚ Ý QUAN TRỌNG:
        1. CHỈ TRẢ VỀ JSON THUẦN TÚY. KHÔNG bọc trong block ```json ... ```, KHÔNG viết thêm bất kỳ lời giải thích nào ngoài chuỗi JSON.
        2. Nếu trong nội dung có từ/cụm từ liên quan trực tiếp đến tên thực thể danh sách cung cấp (như tên khoa khác hoặc giảng viên thuộc khoa), hãy đề xuất liên kết tương ứng vào trường `internal_links` (TỐI ĐA 2 gợi ý tốt nhất). Không tự bịa ra link.
        3. Viết bằng tiếng Việt tự nhiên, trang trọng, chuyên nghiệp.
        """

        system_instruction = "Bạn là trợ lý AI SEO Assistant chuyên nghiệp cho trang giới thiệu khoa/bộ môn trường đại học. Bạn chỉ trả về dữ liệu định dạng JSON hợp lệ."

        ai_response_json = {}
        try:
            raw_ai_response = await ai_service.generate_text(
                prompt=user_prompt,
                system_instruction=system_instruction,
                temperature=0.2,
                max_tokens=800,
                db=db,
                user_id=current_user.id,
                username=current_user.username
            )
            
            clean_response = raw_ai_response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r"^```(?:json)?\n", "", clean_response)
                clean_response = re.sub(r"\n```$", "", clean_response)
                clean_response = clean_response.strip()
                
            ai_response_json = json.loads(clean_response)
            if not isinstance(ai_response_json, dict):
                raise ValueError("AI response is not a JSON object")
        except Exception as e:
            logger.error(f"Failed to fetch/parse Department SEO suggestions: {e}")
            fallback_suggestions = [f"Khắc phục lỗi: {issue.message}" for issue in rules_result.get("issues", [])]
            if not fallback_suggestions:
                fallback_suggestions = ["Trang giới thiệu khoa đã tối ưu SEO khá tốt."]
            ai_response_json = {
                "suggestions": fallback_suggestions,
                "generated_seo_title": seo_title or name,
                "generated_meta_description": seo_description or description,
                "focus_keywords": [focus_keyword] if focus_keyword else [],
                "internal_links": []
            }

        suggestions_list = ai_response_json.get("suggestions", []) or ["Cân nhắc tối ưu hóa các trường thông tin."]
        
        internal_links_list = []
        for link in ai_response_json.get("internal_links", []) or []:
            if link.get("anchor_text") and link.get("url"):
                internal_links_list.append(InternalLinkSuggestion(
                    anchor_text=link.get("anchor_text"),
                    url=link.get("url"),
                    reason=link.get("reason", "Liên kết hữu ích.")
                ))

        def truncate_seo_string(text: str, max_len: int) -> str:
            if not text:
                return ""
            return text[:max_len] + "..." if len(text) > max_len else text

        gen_seo_title = truncate_seo_string(ai_response_json.get("generated_seo_title", ""), 60)
        gen_meta_desc = truncate_seo_string(ai_response_json.get("generated_meta_description", ""), 150)

        return ArticleSEOAnalyzeResponse(
            score=rules_result.get("score", 0),
            status=rules_result.get("status", "warning"),
            issues=rules_result.get("issues", []),
            suggestions=suggestions_list,
            generated_seo_title=gen_seo_title,
            generated_meta_description=gen_meta_desc,
            focus_keywords=ai_response_json.get("focus_keywords", []) or [],
            internal_links=internal_links_list,
            google_preview=google_preview
        )


seo_service = DepartmentSEOService()
