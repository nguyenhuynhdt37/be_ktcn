import re
import json
import uuid
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Comment
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.article.models import Article, ArticleTranslation
from app.modules.language.models import Language
from app.modules.category.models import Category, CategoryTranslation
from app.modules.tag.models import Tag, TagTranslation
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.staff.models import Staff
from app.modules.article.schemas.admin import (
    ArticleSEOAnalyzeRequest,
    ArticleSEOAnalyzeResponse,
    SEOElementAnalysis,
    SEOElementIssue,
    SEOAuditDetails,
    InternalLinkSuggestion,
    GooglePreviewInfo,
    ArticleSEORewriteRequest,
    ArticleSEORewriteResponse,
    ArticleGenerateByIdeaRequest,
    ArticleGenerateByIdeaResponse,
    ArticleSummaryRequest,
    ArticleSummaryResponse,
)
from app.shared.ai import get_ai_service
from app.modules.article.service import slugify


class ArticleSEOService:
    """
    Service độc lập quản lý logic phân tích SEO (SEO Assistant).
    Kết hợp Rule Engine tĩnh để chấm điểm và AI Hub (Gemini) để đưa ra các gợi ý ngữ nghĩa chất lượng cao.
    """

    def _preprocess_content(self, content_html: str) -> Dict[str, Any]:
        """
        Tiền xử lý nội dung HTML để giảm token và tối ưu hóa cho AI:
        1. Parse HTML bằng BeautifulSoup.
        2. Loại bỏ các comment HTML.
        3. Loại bỏ script, style và các thuộc tính hiển thị (class, style, id, data-*).
        4. Loại bỏ Base64 Image string trong thuộc tính src.
        5. Trích xuất thành cấu trúc JSON tinh gọn và text thuần sạch.
        """
        if not content_html:
            return {
                "headings": [],
                "paragraphs": [],
                "links": [],
                "images": [],
                "clean_text": "",
            }

        soup = BeautifulSoup(content_html, "html.parser")

        # 1. Loại bỏ comment
        for comment in soup.find_all(text=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 2. Loại bỏ script và style
        for tag in soup(["script", "style"]):
            tag.extract()

        # 3. Loại bỏ Base64 Image
        images_info = []
        for img in soup.find_all("img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            is_base64 = False
            if src.startswith("data:"):
                is_base64 = True
                img["src"] = ""  # Strip base64 data to save tokens
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
        headings = []
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            headings.append(f"{h.name.upper()}: {h.get_text().strip()}")

        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)

        links_info = []
        for a in soup.find_all("a"):
            href = a.get("href", "")
            text = a.get_text().strip()
            if href:
                links_info.append({"text": text, "url": href})

        # 6. Trích xuất text sạch cho việc tính toán mật độ từ khóa
        clean_text = soup.get_text(separator=" ")
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return {
            "headings": headings,
            "paragraphs": paragraphs,
            "links": links_info,
            "images": images_info,
            "clean_text": clean_text,
        }

    def _run_rule_engine(
        self,
        title: str,
        excerpt: str,
        seo_title: str,
        seo_description: str,
        slug: str,
        thumbnail_object_key: Optional[str],
        preprocessed: Dict[str, Any],
        focus_keyword: Optional[str]
    ) -> Dict[str, Any]:
        """
        Rule Engine chấm điểm tĩnh (tối đa 100 điểm) và phát hiện các vấn đề kỹ thuật cơ bản.
        """
        issues: List[SEOElementIssue] = []
        title_issues: List[SEOElementIssue] = []
        meta_issues: List[SEOElementIssue] = []
        content_issues: List[SEOElementIssue] = []
        link_issues: List[SEOElementIssue] = []

        # --- 1. TITLE ANALYSIS (Tối đa 15 điểm) ---
        title_score = 15
        eval_title = seo_title or title
        if not eval_title:
            title_score = 0
            title_issues.append(SEOElementIssue(type="missing_title", message="Thiếu tiêu đề bài viết hoặc tiêu đề SEO."))
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
        eval_desc = seo_description or excerpt
        if not eval_desc:
            meta_score = 0
            meta_issues.append(SEOElementIssue(type="missing_meta_description", message="Thiếu mô tả SEO hoặc tóm tắt bài viết."))
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

        # --- 3. FEATURED IMAGE & SLUG & SUMMARY (Tối đa 25 điểm) ---
        # Featured Image (10đ)
        image_score = 10
        if not thumbnail_object_key:
            image_score = 0
            issues.append(SEOElementIssue(type="missing_featured_image", message="Bài viết chưa có ảnh đại diện (Featured Image)."))
        
        # Summary (10đ)
        summary_score = 10
        if not excerpt:
            summary_score = 0
            issues.append(SEOElementIssue(type="missing_summary", message="Bài viết chưa có tóm tắt (Excerpt)."))
        elif len(excerpt) < 50:
            summary_score = 5
            issues.append(SEOElementIssue(type="summary_too_short", message="Tóm tắt bài viết quá ngắn (dưới 50 ký tự)."))

        # Slug (5đ)
        slug_score = 5
        if not slug:
            slug_score = 0
            issues.append(SEOElementIssue(type="missing_slug", message="Bài viết chưa cấu hình Slug."))
        else:
            # Kiểm tra định dạng slug chuẩn URL (chữ cái thường không dấu, số, dấu gạch ngang)
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
                slug_score = 2
                issues.append(SEOElementIssue(
                    type="invalid_slug", 
                    message="Slug không chuẩn URL. Chỉ được chứa chữ thường không dấu, số và dấu gạch ngang (ví dụ: 'tuyen-sinh-dai-hoc')."
                ))

        # --- 4. CONTENT & HEADING ANALYSIS (Tối đa 30 điểm) ---
        content_score = 30
        
        # Phân tích Heading
        headings = preprocessed.get("headings", [])
        h2_count = sum(1 for h in headings if h.startswith("H2:"))
        h1_in_content = sum(1 for h in headings if h.startswith("H1:"))
        
        heading_penalty = 0
        if h2_count == 0:
            heading_penalty += 10
            content_issues.append(SEOElementIssue(
                type="missing_h2", 
                message="Nội dung thiếu tiêu đề phụ H2. Nên có ít nhất một thẻ H2 để cấu trúc bài viết rõ ràng."
            ))
        if h1_in_content > 0:
            heading_penalty += 5
            content_issues.append(SEOElementIssue(
                type="duplicate_h1", 
                message="Nội dung chứa thẻ H1. Tiêu đề bài viết đã là H1, tránh lặp lại H1 trong nội dung."
            ))
            
        content_score = max(0, content_score - heading_penalty)

        # Phân tích Image Alt Text
        images = preprocessed.get("images", [])
        if images:
            missing_alt_count = sum(1 for img in images if not img.get("alt", "").strip())
            if missing_alt_count > 0:
                alt_penalty = int(10 * (missing_alt_count / len(images)))
                content_score = max(0, content_score - alt_penalty)
                content_issues.append(SEOElementIssue(
                    type="missing_image_alt", 
                    message=f"Có {missing_alt_count}/{len(images)} hình ảnh trong bài viết chưa được điền thẻ mô tả Alt text."
                ))

        # Phân tích Số từ
        clean_text = preprocessed.get("clean_text", "")
        word_count = len(clean_text.split()) if clean_text else 0
        if word_count < 300:
            content_score = max(0, content_score - 10)
            content_issues.append(SEOElementIssue(
                type="content_too_short", 
                message=f"Bài viết quá ngắn ({word_count} từ). Nên viết tối thiểu 300 từ để được Google đánh giá cao."
            ))

        # Phân tích Keyword Density (Mật độ từ khóa)
        keyword_density = 0.0
        if focus_keyword:
            if len(focus_keyword) > 40 or len(focus_keyword.split()) > 7:
                issues.append(SEOElementIssue(
                    type="focus_keyword_too_long",
                    message=f"Từ khóa chính quá dài ({len(focus_keyword)} ký tự). Từ khóa chính (Focus Keyword) nên là một cụm từ ngắn gọn (2-5 từ, ví dụ: 'tình nguyện hè') để tối ưu hóa SEO tốt nhất."
                ))

        if focus_keyword and word_count > 0:
            keyword_count = len(re.findall(re.escape(focus_keyword.lower()), clean_text.lower()))
            keyword_density = (keyword_count / word_count) * 100
            
            # Cảnh báo mật độ từ khóa
            if keyword_density == 0.0:
                content_issues.append(SEOElementIssue(
                    type="keyword_not_found", 
                    message=f"Từ khóa chính '{focus_keyword}' không xuất hiện lần nào trong nội dung bài viết."
                ))
            elif keyword_density < 0.5:
                content_issues.append(SEOElementIssue(
                    type="keyword_density_low", 
                    message=f"Mật độ từ khóa chính quá thấp ({keyword_density:.2f}%). Khuyên dùng từ 0.5% - 2.5%."
                ))
            elif keyword_density > 3.5:
                content_issues.append(SEOElementIssue(
                    type="keyword_density_high", 
                    message=f"Mật độ từ khóa quá cao ({keyword_density:.2f}%) - dấu hiệu nhồi nhét từ khóa (Keyword Stuffing). Hãy giảm bớt."
                ))
                
            # Kiểm tra từ khóa trong thẻ H2
            if focus_keyword.lower() not in "".join(headings).lower():
                content_issues.append(SEOElementIssue(
                    type="keyword_missing_heading", 
                    message=f"Từ khóa chính '{focus_keyword}' chưa xuất hiện ở bất kỳ tiêu đề phụ H2/H3 nào."
                ))

        # --- 5. LINK ANALYSIS (Tối đa 15 điểm) ---
        link_score = 15
        links = preprocessed.get("links", [])
        
        internal_link_count = 0
        external_link_count = 0
        
        for link in links:
            url = link.get("url", "").lower()
            # Liên kết nội bộ nếu bắt đầu bằng / hoặc chứa tên miền chính
            if url.startswith("/") or "ktcn.edu.vn" in url or "localhost" in url:
                internal_link_count += 1
            else:
                external_link_count += 1
                
        if internal_link_count == 0:
            link_score = max(0, link_score - 10)
            link_issues.append(SEOElementIssue(
                type="missing_internal_link", 
                message="Thiếu liên kết nội bộ. Hãy thêm liên kết tới các trang tuyển sinh, giới thiệu khoa khác của trường."
            ))
            
        if external_link_count == 0:
            link_score = max(0, link_score - 5)
            link_issues.append(SEOElementIssue(
                type="missing_external_link", 
                message="Thiếu liên kết ngoài. Nên thêm liên kết tham chiếu tới các trang uy tín (như Bộ GDĐT, v.v.)."
            ))

        # --- TỔNG HỢP KẾT QUẢ ---
        total_score = title_score + meta_score + image_score + summary_score + slug_score + content_score + link_score
        
        # Xác định trạng thái SEO
        if total_score >= 80:
            status = "good"
        elif total_score >= 50:
            status = "warning"
        else:
            status = "error"

        # Gộp tất cả các issues
        all_issues = issues + title_issues + meta_issues + content_issues + link_issues

        # Xây dựng các Element Analysis cụ thể
        title_analysis = SEOElementAnalysis(
            score=int(title_score * (100 / 15)),
            status="good" if title_score == 15 else ("warning" if title_score >= 10 else "error"),
            message="Tiêu đề SEO đạt độ dài tối ưu và chứa từ khóa." if title_score == 15 else "Tiêu đề SEO cần được tối ưu thêm.",
            issues=title_issues
        )
        
        meta_analysis = SEOElementAnalysis(
            score=int(meta_score * (100 / 15)),
            status="good" if meta_score == 15 else ("warning" if meta_score >= 10 else "error"),
            message="Mô tả SEO đạt độ dài lý tưởng và có từ khóa chính." if meta_score == 15 else "Mô tả SEO cần được cải thiện.",
            issues=meta_issues
        )
        
        content_analysis = SEOElementAnalysis(
            score=int(content_score * (100 / 30)),
            status="good" if content_score >= 25 else ("warning" if content_score >= 15 else "error"),
            message="Nội dung trình bày khoa học, heading và alt text đầy đủ." if content_score >= 25 else "Nội dung cần tối ưu cấu trúc headings hoặc alt text.",
            issues=content_issues
        )
        
        link_analysis = SEOElementAnalysis(
            score=int(link_score * (100 / 15)),
            status="good" if link_score == 15 else ("warning" if link_score >= 5 else "error"),
            message="Đầy đủ liên kết nội bộ và liên kết ngoài." if link_score == 15 else "Thiếu liên kết nội bộ hoặc liên kết ngoài.",
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
        Truy vấn nhanh các thực thể chính trong DB để cung cấp danh sách link nội bộ tiềm năng cho AI so khớp.
        """
        targets = []
        try:
            # 1. Tìm language_id tương ứng
            lang_stmt = select(Language.id).where(Language.code == lang_code, Language.is_active == True)
            lang_res = await db.execute(lang_stmt)
            lang_id = lang_res.scalar_one_or_none()
            if not lang_id:
                # Dự phòng ngôn ngữ mặc định
                lang_stmt = select(Language.id).where(Language.is_default == True)
                lang_res = await db.execute(lang_stmt)
                lang_id = lang_res.scalar_one_or_none()

            # 2. Truy vấn Categories
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

            # 3. Truy vấn Tags
            if lang_id:
                tag_stmt = select(TagTranslation.name, TagTranslation.slug).where(
                    TagTranslation.language_id == lang_id
                ).limit(15)
                tag_res = await db.execute(tag_stmt)
                for name, slug in tag_res.all():
                    targets.append({
                        "name": name,
                        "url": f"/portal/tags/{slug}",
                        "type": "Thẻ bài viết"
                    })

            # 4. Truy vấn Departments (Khoa / Phòng ban)
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

            # 5. Truy vấn Staffs (Giảng viên / Nhân sự)
            # Staff full_name và slug nằm trực tiếp ở bảng Staff
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
            # Danh sách dự phòng cứng nếu có lỗi DB
            targets = [
                {"name": "Trang chủ", "url": "/", "type": "Trang chính"},
                {"name": "Tuyển sinh", "url": "/portal/categories/tuyen-sinh", "type": "Danh mục"},
                {"name": "Đào tạo", "url": "/portal/categories/dao-tao", "type": "Danh mục"},
                {"name": "Giới thiệu khoa", "url": "/portal/departments/gioi-thieu", "type": "Khoa"},
            ]
        
        return targets

    async def analyze_article(
        self,
        db: AsyncSession,
        article_id: uuid.UUID,
        payload: ArticleSEOAnalyzeRequest,
        current_user: Any,
    ) -> ArticleSEOAnalyzeResponse:
        """
        Thực hiện phân tích SEO cho bài viết dựa trên Rule Engine và gọi AI Hub (Gemini) để sinh gợi ý.
        """
        # 1. Tìm thông tin trong DB để làm giá trị mặc định / bổ sung
        article = None
        translation = None
        
        try:
            stmt = select(Article).where(Article.id == article_id)
            res = await db.execute(stmt)
            article = res.scalar_one_or_none()
            
            if article:
                lang_stmt = select(Language.id).where(Language.code == payload.lang)
                lang_res = await db.execute(lang_stmt)
                lang_id = lang_res.scalar_one_or_none()
                
                if lang_id:
                    trans_stmt = select(ArticleTranslation).where(
                        ArticleTranslation.article_id == article_id,
                        ArticleTranslation.language_id == lang_id
                    )
                    trans_res = await db.execute(trans_stmt)
                    translation = trans_res.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"DB lookup failed for article {article_id}: {e}. Proceeding with payload only.")

        # 2. Merge dữ liệu payload và DB
        title = payload.title if payload.title is not None else (translation.title if translation else "")
        content = payload.content if payload.content is not None else (translation.content if translation else "")
        excerpt = payload.excerpt if payload.excerpt is not None else (translation.excerpt if translation else "")
        seo_title = payload.seo_title if payload.seo_title is not None else (translation.seo_title if translation else "")
        seo_description = payload.seo_description if payload.seo_description is not None else (translation.seo_description if translation else "")
        slug = payload.slug if payload.slug is not None else (translation.slug if translation else slugify(title))
        thumbnail_object_key = payload.thumbnail_object_key if payload.thumbnail_object_key is not None else (article.thumbnail_object_key if article else None)
        focus_keyword = payload.focus_keyword

        # 3. Tiền xử lý nội dung HTML -> Structured JSON
        preprocessed = self._preprocess_content(content)

        # 4. Tính toán điểm SEO & phát hiện lỗi bằng Rule Engine tĩnh
        rules_result = self._run_rule_engine(
            title=title,
            excerpt=excerpt,
            seo_title=seo_title,
            seo_description=seo_description,
            slug=slug,
            thumbnail_object_key=thumbnail_object_key,
            preprocessed=preprocessed,
            focus_keyword=focus_keyword
        )

        # Chuẩn bị Google Preview
        google_title = seo_title or title or "Tiêu đề bài viết..."
        google_desc = seo_description or excerpt or "Mô tả bài viết hiển thị trên Google..."
        google_url = f"https://ktcn.edu.vn/portal/articles/{slug}" if slug else "https://ktcn.edu.vn/portal/articles/slug-bai-viet"
        google_preview = GooglePreviewInfo(
            title=google_title[:70] + "..." if len(google_title) > 70 else google_title,
            url=google_url,
            description=google_desc[:160] + "..." if len(google_desc) > 160 else google_desc
        )

        # 5. Lấy danh sách link nội bộ tiềm năng làm ngữ cảnh cho AI
        internal_targets = await self._get_internal_link_targets(db, payload.lang)

        # 6. Gọi AI Hub (Gemini) qua AIService
        ai_service = get_ai_service()
        
        # Xây dựng prompt chi tiết
        user_prompt = f"""
        Bạn là một chuyên gia tối ưu hóa công cụ tìm kiếm (SEO Specialist) cho website trường Đại học.
        Hãy phân tích dữ liệu bài viết đã được tiền xử lý dưới đây và đưa ra các đánh giá chất lượng sâu sắc, đề xuất cải thiện cụ thể.

        THÔNG TIN BÀI VIẾT:
        - Tiêu đề: {title}
        - Tóm tắt: {excerpt}
        - Tiêu đề SEO hiện tại: {seo_title or '(Chưa có)'}
        - Mô tả SEO hiện tại: {seo_description or '(Chưa có)'}
        - Từ khóa chính người soạn muốn tập trung: {focus_keyword or '(Chưa nhập)'}

        CẤU TRÚC NỘI DUNG CHI TIẾT (ĐÃ TIỀN XỬ LÝ):
        - Các Tiêu đề phụ (Headings): {json.dumps(preprocessed.get("headings", []), ensure_ascii=False)}
        - Danh sách các Đoạn văn (tóm tắt): {json.dumps(preprocessed.get("paragraphs", [])[:8], ensure_ascii=False)} (hiển thị 8 đoạn đầu để phân tích ngữ nghĩa)
        - Tổng số từ: {len(preprocessed.get("clean_text", "").split())} từ.
        - Mật độ xuất hiện từ khóa chính thực tế: {rules_result.get("keyword_density"):.2f}%.

        KẾT QUẢ PHÂN TÍCH TĨNH TỪ HỆ THỐNG:
        - Điểm SEO tính được: {rules_result.get("score")}/100.
        - Các lỗi kỹ thuật phát hiện: {[issue.message for issue in rules_result.get("issues")]}

        DANH SÁCH CÁC THỰC THỂ KHẢ DỤNG ĐỂ GỢI Ý LIÊN KẾT NỘI BỘ (INTERNAL LINK):
        {json.dumps(internal_targets, ensure_ascii=False)}

        YÊU CẦU ĐỐI VỚI BẠN:
        Hãy trả về kết quả dạng JSON khớp chính xác với cấu trúc dưới đây để backend xử lý:
        {{
            "suggestions": [
                "Mảng chứa TỐI ĐA 4 gợi ý cải thiện, viết thật ngắn gọn, súc tích (dưới 15 từ mỗi gợi ý)."
            ],
            "generated_seo_title": "Tiêu đề SEO mới tối ưu hơn (dài 45-65 ký tự, chứa từ khóa chính, hấp dẫn người đọc)",
            "generated_meta_description": "Mô tả SEO mới tối ưu hơn (dài 120-160 ký tự, chứa từ khóa chính, có lời kêu gọi hành động)",
            "focus_keywords": [
                "Mảng chứa TỐI ĐA 2 từ khóa phụ/từ khóa liên quan tiềm năng rút ra từ nội dung bài viết."
            ],
            "internal_links": [
                {{
                    "anchor_text": "Cụm từ chính xác có xuất hiện trong nội dung bài viết mà bạn khuyên nên gắn link",
                    "url": "Đường dẫn URL tương ứng lấy từ danh sách thực thể được cung cấp ở trên",
                    "reason": "Lý do ngắn gọn tại sao nên chèn liên kết này ở vị trí đó"
                }}
            ]
        }}

        CHÚ Ý QUAN TRỌNG:
        1. CHỈ TRẢ VỀ JSON THUẦN TÚY. KHÔNG bọc trong block ```json ... ```, KHÔNG viết thêm bất kỳ lời giải thích nào ngoài chuỗi JSON.
        2. Nếu trong nội dung bài viết có xuất hiện các từ/cụm từ khớp hoặc liên quan đến tên các thực thể trong danh sách, hãy đề xuất liên kết tương ứng vào trường `internal_links` (TỐI ĐA 2 gợi ý chất lượng nhất). Không tự bịa ra link không có trong danh sách.
        3. Hãy viết bằng tiếng Việt tự nhiên, ngắn gọn và có tính chuyên môn cao.
        """

        system_instruction = "Bạn là trợ lý AI SEO Assistant chuyên nghiệp cho hệ thống CMS trường đại học. Bạn chỉ trả về dữ liệu định dạng JSON hợp lệ."

        ai_response_json = {}
        try:
            # Gọi trực tiếp qua AIService
            raw_ai_response = await ai_service.generate_text(
                prompt=user_prompt,
                system_instruction=system_instruction,
                temperature=0.2, # Đảm bảo đầu ra JSON ổn định
                max_tokens=800,  # Giới hạn token đầu ra để phản hồi nhanh nhất, tránh timeout
                db=db,
                user_id=current_user.id,
                username=current_user.username
            )
            
            # Làm sạch chuỗi phản hồi từ AI đề phòng có markdown block
            clean_response = raw_ai_response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r"^```(?:json)?\n", "", clean_response)
                clean_response = re.sub(r"\n```$", "", clean_response)
                clean_response = clean_response.strip()
                
            ai_response_json = json.loads(clean_response)
            logger.info("Successfully parsed SEO Assistant response from AI Hub.")
        except Exception as e:
            logger.error(f"Failed to fetch or parse SEO suggestions from AI Hub: {e}. Falling back to Rule Engine suggestions.")
            # Tạo fallback tự động từ kết quả Rule Engine
            fallback_suggestions = []
            for issue in rules_result.get("issues", []):
                fallback_suggestions.append(f"Khắc phục lỗi: {issue.message}")
            if not fallback_suggestions:
                fallback_suggestions = ["Bài viết của bạn đã tối ưu SEO khá tốt. Hãy tiếp tục phát huy!"]
                
            ai_response_json = {
                "suggestions": fallback_suggestions,
                "generated_seo_title": seo_title or title or "",
                "generated_meta_description": seo_description or excerpt or "",
                "focus_keywords": [focus_keyword] if focus_keyword else [],
                "internal_links": []
            }

        # 7. Tổng hợp kết quả trả về khớp chính xác với ArticleSEOAnalyzeResponse Schema
        suggestions_list = ai_response_json.get("suggestions", [])
        if not suggestions_list:
            suggestions_list = ["Cân nhắc tối ưu hóa độ dài tiêu đề và mô tả theo khuyến nghị của Google."]

        internal_links_list = []
        for link in ai_response_json.get("internal_links", []):
            if link.get("anchor_text") and link.get("url"):
                internal_links_list.append(InternalLinkSuggestion(
                    anchor_text=link.get("anchor_text"),
                    url=link.get("url"),
                    reason=link.get("reason", "Liên kết hữu ích.")
                ))

        gen_seo_title = self._truncate_seo_string(ai_response_json.get("generated_seo_title", ""), 60)
        gen_meta_desc = self._truncate_seo_string(ai_response_json.get("generated_meta_description", ""), 150)

        return ArticleSEOAnalyzeResponse(
            score=rules_result.get("score", 0),
            status=rules_result.get("status", "warning"),
            issues=rules_result.get("issues", []),
            suggestions=suggestions_list,
            generated_seo_title=gen_seo_title,
            generated_meta_description=gen_meta_desc,
            focus_keywords=ai_response_json.get("focus_keywords", []),
            internal_links=internal_links_list,
            google_preview=google_preview
        )

    def _truncate_seo_string(self, text: str, max_len: int) -> str:
        """
        Cắt ngắn chuỗi SEO (Title/Description) thông minh theo ranh giới từ (word boundary)
        để không bị cụt chữ giữa chừng và luôn đảm bảo độ dài dưới giới hạn yêu cầu.
        """
        text = text.strip().strip('"\'')
        if len(text) <= max_len:
            return text
        
        # Cắt thô
        truncated = text[:max_len - 3]
        # Tìm khoảng trắng cuối cùng để tránh cắt đôi từ
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
            
        return truncated.strip() + "..."

    def _extract_and_replace_base64(self, html_content: str) -> tuple[str, dict[str, str]]:
        """
        Trích xuất toàn bộ ảnh base64 trong HTML thành placeholders đặc biệt để tiết kiệm token gửi AI Hub.
        """
        if not html_content:
            return "", {}
        
        soup = BeautifulSoup(html_content, "html.parser")
        base64_map = {}
        placeholder_idx = 0
        
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src.startswith("data:image/") and ";base64," in src:
                placeholder = f"BASE64_IMG_PLACEHOLDER_{placeholder_idx}"
                base64_map[placeholder] = src
                img["src"] = placeholder
                placeholder_idx += 1
                
        return str(soup), base64_map

    def _restore_base64(self, html_content: str, base64_map: dict[str, str]) -> str:
        """
        Khôi phục lại các chuỗi base64 ban đầu vào vị trí của placeholders trong HTML kết quả.
        """
        if not html_content or not base64_map:
            return html_content
            
        restored = html_content
        for placeholder, base64_data in base64_map.items():
            restored = restored.replace(placeholder, base64_data)
            
        return restored

    async def rewrite_article(
        self,
        db: AsyncSession,
        payload: ArticleSEORewriteRequest,
        current_user: Any
    ) -> ArticleSEORewriteResponse:
        """
        Viết lại bài viết dạng HTML để tối ưu hóa SEO và văn phong, bảo toàn ảnh base64.
        Tự động khắc phục các lỗi SEO như thiếu tiêu đề phụ H2, thiếu link nội bộ và link ngoài.
        """
        # 1. Bóc tách base64 images
        clean_html, base64_map = self._extract_and_replace_base64(payload.content)
        
        # 2. Truy vấn danh sách thực thể nội bộ khả dụng để AI chèn link tự động
        internal_targets = await self._get_internal_link_targets(db, payload.lang)
        
        # 3. Gọi AI Hub để viết lại bài viết
        ai_service = get_ai_service()
        
        system_instruction = (
            "Bạn là chuyên gia biên tập nội dung (Content Editor) và tối ưu SEO chuyên nghiệp cho website trường Đại học. "
            "Bạn chuyên viết lại bài viết để tối ưu hóa SEO và cải thiện văn phong. "
            "Bạn BẮT BUỘC phải giữ nguyên cấu trúc HTML ban đầu (tất cả các thẻ như <p>, <img>, <a>, v.v.), "
            "giữ nguyên các giá trị thuộc tính src của hình ảnh (bao gồm cả các placeholder có dạng BASE64_IMG_PLACEHOLDER_X) "
            "và các thuộc tính href của các liên kết cũ. Chỉ tối ưu hóa phần nội dung văn bản hiển thị."
        )
        
        keyword_instruction = ""
        if payload.focus_keyword:
            keyword_instruction = f'2. Tự nhiên chèn thêm từ khóa chính: "{payload.focus_keyword}" nếu cần thiết để tăng mật độ từ khóa hợp lý (khoảng 1% - 2%).'
        else:
            keyword_instruction = "2. Tập trung tối ưu hóa câu chữ, sửa lỗi ngữ pháp và không cần chèn thêm từ khóa chính cụ thể nào."

        prompt = f"""
        Hãy viết lại nội dung HTML dưới đây để tối ưu hóa chất lượng SEO và văn phong:
        
        NỘI DUNG HTML CẦN VIẾT LẠI:
        {clean_html}

        DANH SÁCH THỰC THỂ KHẢ DỤNG ĐỂ GỢI Ý LIÊN KẾT NỘI BỘ (INTERNAL LINK):
        {json.dumps(internal_targets, ensure_ascii=False)}

        YÊU CẦU CHI TIẾT KHI VIẾT LẠI:
        1. Tối ưu hóa văn phong theo phong cách: {payload.tone}.
        {keyword_instruction}
        3. CẤU TRÚC TIÊU ĐỀ PHỤ: Hãy đảm bảo bài viết có các tiêu đề phụ rõ ràng. Hãy chuyển đổi các tiêu đề phụ đang viết dạng in đậm (ví dụ: `<p><strong>Tiêu đề phụ</strong></p>`) thành thẻ HTML tiêu đề chuẩn `<h2>` hoặc `<h3>` để cấu trúc bài viết chuẩn SEO.
        4. CHÈN LIÊN KẾT NỘI BỘ (INTERNAL LINK): Duyệt qua danh sách thực thể khả dụng ở trên. Nếu trong nội dung có nhắc đến hoặc liên quan đến tên các thực thể này, hãy tự động chèn liên kết tương ứng bằng thẻ `<a href="đường-dẫn-của-thực-thể">tên thực thể hoặc cụm từ tương ứng</a>`. Tối đa chèn 2-3 liên kết nội bộ tự nhiên, hợp ngữ cảnh.
        5. CHÈN LIÊN KẾT NGOÀI (EXTERNAL LINK): Tự động bổ sung 1 liên kết ngoài uy tín (thẻ `<a href="https://..." target="_blank">...</a>` ví dụ dẫn tới trang Bộ Giáo dục và Đào tạo, Đoàn thanh niên, hoặc trang báo chí lớn) phù hợp với ngữ cảnh bài viết để tăng điểm SEO tin cậy.
        6. KHÔNG viết thêm bất kỳ lời bình luận hay giải thích nào, KHÔNG bọc trong khối ```html ... ```. Chỉ trả về chuỗi HTML kết quả duy nhất.
        """
        
        try:
            raw_response = await ai_service.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_tokens=2500,  # Tránh cắt cụt bài viết
                db=db,
                user_id=current_user.id,
                username=current_user.username
            )
            
            # Làm sạch phản hồi
            new_content = raw_response.strip()
            if new_content.startswith("```"):
                new_content = re.sub(r"^```(?:html)?\n", "", new_content)
                new_content = re.sub(r"\n```$", "", new_content)
                new_content = new_content.strip()
                
            # 3. Khôi phục base64 images
            final_content = self._restore_base64(new_content, base64_map)
            return ArticleSEORewriteResponse(content=final_content)
            
        except Exception as e:
            logger.error(f"Failed to rewrite article using AI Hub: {e}")
            # Fallback: Trả về nội dung gốc nếu lỗi
            return ArticleSEORewriteResponse(content=payload.content)

    async def generate_by_idea(
        self,
        db: AsyncSession,
        payload: ArticleGenerateByIdeaRequest,
        current_user: Any
    ) -> ArticleGenerateByIdeaResponse:
        """
        Tự động tạo toàn bộ bài viết từ ý tưởng/dàn ý thô.
        """
        ai_service = get_ai_service()
        
        system_instruction = (
            "Bạn là chuyên gia sáng tạo nội dung (Content Creator) và SEO Specialist chuyên nghiệp cho website trường Đại học. "
            "Bạn luôn trả về dữ liệu định dạng JSON hợp lệ phù hợp với schema yêu cầu."
        )
        
        prompt = f"""
        Dựa trên mô tả ý tưởng/dàn ý dưới đây, hãy sinh một bài viết hoàn chỉnh chuẩn SEO cho website trường Đại học.
        
        Ý TƯỞNG BÀI VIẾT:
        "{payload.idea}"
        
        TỪ KHÓA CHÍNH MONG MUỐN:
        "{payload.focus_keyword or '(Tự đề xuất từ khóa phù hợp)'}"
        
        VĂN PHONG BÀI VIẾT:
        "{payload.tone}"
        
        YÊU CẦU CHI TIẾT:
        1. Tiêu đề (title): Đặt tiêu đề hấp dẫn, chứa từ khóa chính, dưới 70 ký tự.
        2. Tóm tắt (excerpt): Viết mô tả ngắn súc tích, khoảng 80-130 ký tự.
        3. Nội dung (content): Sinh nội dung chi tiết dạng HTML. Nội dung phải đầy đủ (tối thiểu 350-500 từ), sử dụng cấu trúc tiêu đề phụ H2/H3 hợp lý. Bạn có thể tự đề xuất một số chi tiết, ngày tháng, thông tin liên hệ, hoặc chèn ảnh minh họa giả định (sử dụng placeholder src="https://picsum.photos/800/600" với alt đầy đủ mô tả ảnh) để bài viết sinh động.
        4. Tiêu đề SEO (seo_title): Gợi ý tiêu đề SEO tối ưu, dài 45-65 ký tự, chứa từ khóa chính.
        5. Mô tả SEO (seo_description): Mô tả SEO tối ưu hiển thị trên Google, dài 120-160 ký tự.
        6. Slug: Sinh slug chuẩn URL không dấu, phân cách bởi dấu gạch ngang (ví dụ: 'khai-giang-lop-hoc-vo-co-truyen').

        HÃY TRẢ VỀ KẾT QUẢ DẠNG JSON KHỚP CHÍNH XÁC VỚI CẤU TRÚC SAU:
        {{
            "title": "Tiêu đề bài viết",
            "excerpt": "Tóm tắt bài viết",
            "content": "Nội dung bài viết hoàn chỉnh dạng HTML",
            "seo_title": "Tiêu đề SEO",
            "seo_description": "Mô tả SEO",
            "slug": "slug-bai-viet"
        }}

        CHÚ Ý QUAN TRỌNG:
        - CHỈ TRẢ VỀ JSON THUẦN TÚY. KHÔNG bọc trong block ```json ... ```, KHÔNG viết thêm bất kỳ lời giải thích nào ngoài chuỗi JSON.
        - Viết bằng tiếng Việt trôi chảy, chuyên nghiệp, thông tin khoa học và nhất quán.
        """
        
        try:
            raw_response = await ai_service.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.7,
                max_tokens=3000,
                db=db,
                user_id=current_user.id,
                username=current_user.username
            )
            
            clean_response = raw_response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r"^```(?:json)?\n", "", clean_response)
                clean_response = re.sub(r"\n```$", "", clean_response)
                clean_response = clean_response.strip()
                
            data = json.loads(clean_response)
            
            # Đảm bảo slug chuẩn URL nếu AI trả về không chuẩn
            slug_val = data.get("slug", "")
            if not slug_val:
                slug_val = slugify(data.get("title", ""))
            else:
                slug_val = slugify(slug_val)
                
            gen_seo_title = self._truncate_seo_string(data.get("seo_title", data.get("title", "")), 60)
            gen_seo_desc = self._truncate_seo_string(data.get("seo_description", data.get("excerpt", "")), 150)

            return ArticleGenerateByIdeaResponse(
                title=data.get("title", "Bài viết mới"),
                excerpt=data.get("excerpt", "Tóm tắt bài viết"),
                content=data.get("content", "<p>Nội dung đang được cập nhật...</p>"),
                seo_title=gen_seo_title,
                seo_description=gen_seo_desc,
                slug=slug_val
            )
            
        except Exception as e:
            logger.error(f"Failed to generate article from idea using AI Hub: {e}")
            title_fallback = f"Bài viết về: {payload.idea[:40]}..."
            return ArticleGenerateByIdeaResponse(
                title=title_fallback,
                excerpt=payload.idea[:120],
                content=f"<p>Ý tưởng: {payload.idea}</p><p>Hệ thống không thể kết nối tới AI để tự động tạo bài viết tại thời điểm này. Vui lòng thử lại sau.</p>",
                seo_title=title_fallback,
                seo_description=payload.idea[:120],
                slug=slugify(title_fallback)
            )

    async def summarize_article(
        self,
        db: AsyncSession,
        payload: ArticleSummaryRequest,
        current_user: Any
    ) -> ArticleSummaryResponse:
        """
        Sử dụng AI tự động tóm tắt bài viết dạng text thuần túy (không HTML) để làm Excerpt/Tóm tắt.
        """
        # Trích xuất text sạch
        soup = BeautifulSoup(payload.content, "html.parser")
        clean_text = soup.get_text(separator=" ").strip()
        
        # Cắt bớt text thô nếu quá dài để tiết kiệm tokens
        words = clean_text.split()
        if len(words) > 1000:
            clean_text = " ".join(words[:1000]) + "..."
            
        ai_service = get_ai_service()
        
        system_instruction = (
            "Bạn là trợ lý biên tập chuyên nghiệp. Nhiệm vụ của bạn là viết một đoạn tóm tắt bài viết ngắn gọn, "
            "súc tích và thu hút người đọc. Bạn chỉ trả về nội dung tóm tắt dạng văn bản thuần túy (Plain Text), "
            "không chứa bất kỳ thẻ HTML nào, không chứa markdown, không viết thêm lời giải thích nào khác."
        )
        
        max_words = payload.max_length or 100
        prompt = f"""
        Hãy tóm tắt bài viết dưới đây thành một đoạn văn ngắn gọn, súc tích (dưới {max_words} từ) để làm phần tóm tắt chính thức của bài viết.
        
        YÊU CẦU:
        1. Đoạn tóm tắt phải phản ánh chính xác nội dung chính và thông điệp của bài viết.
        2. Độ dài tối đa: {max_words} từ (words).
        3. Phải là một câu hoặc đoạn văn hoàn chỉnh, kết thúc bằng dấu chấm câu (.), KHÔNG viết dở dang, KHÔNG chứa dấu ba chấm (...) ở cuối.
        4. Tuyệt đối không trả về bất kỳ định dạng HTML, không markdown, không viết lời giải thích nào ngoài nội dung tóm tắt.
        
        NỘI DUNG BÀI VIẾT:
        {clean_text}
        """
        
        try:
            raw_response = await ai_service.generate_text(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_tokens=400,
                db=db,
                user_id=current_user.id,
                username=current_user.username
            )
            
            summary = raw_response.strip().strip('"\'')
            
            # Loại bỏ dấu ba chấm ở cuối nếu AI sinh ra
            if summary.endswith("..."):
                summary = summary[:-3].strip()
            elif summary.endswith(".."):
                summary = summary[:-2].strip()
                
            # Đảm bảo kết thúc bằng dấu chấm câu nếu bị AI bỏ quên
            if summary and summary[-1] not in ['.', '!', '?']:
                summary += "."
                
            # Khống chế số từ tối đa nếu AI sinh quá dài
            words = summary.split()
            if len(words) > max_words:
                summary = " ".join(words[:max_words])
                # Tìm dấu chấm câu gần cuối nhất để cắt câu tự nhiên
                for punc in ['.', '!', '?']:
                    last_punc = summary.rfind(punc)
                    if last_punc > len(summary) * 0.7:
                        summary = summary[:last_punc + 1]
                        break
                if summary and summary[-1] not in ['.', '!', '?']:
                    summary += "."
                    
            return ArticleSummaryResponse(summary=summary)
            
        except Exception as e:
            logger.error(f"Failed to summarize article content using AI Hub: {e}")
            fallback_words = clean_text.split()[:max_words]
            fallback_text = " ".join(fallback_words)
            if fallback_text and fallback_text[-1] not in ['.', '!', '?']:
                fallback_text += "."
            return ArticleSummaryResponse(summary=fallback_text)


# Khởi tạo instance toàn cục
seo_service = ArticleSEOService()
