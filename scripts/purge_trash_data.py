import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, and_, or_, delete

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.position.models import Position, PositionTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.staff.models import Staff, StaffTranslation

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.banner.models import Banner
from app.modules.ai_hub.models import AIRequestLog
from app.modules.statistics.models import SystemStatistics
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import MenuItem, MenuItemTranslation
from app.modules.article.models import Article
from app.modules.tag.models import Tag

async def main():
    async with SessionLocal() as db:
        print("Bắt đầu dọn dẹp dữ liệu rác...")

        # 1. Xóa cứng toàn bộ Staffs đã bị soft-delete (is_active=False hoặc deleted_at is not null)
        # Các staff này là dữ liệu test (Nguyễn Văn A, Lưu Văn Phúc, Nguyễn Hoa Lư...) hoặc staff trùng lặp đã chuẩn hóa.
        stmt_staff_del = select(Staff).where(
            or_(Staff.is_active == False, Staff.deleted_at != None)
        )
        inactive_staffs = (await db.execute(stmt_staff_del)).scalars().all()
        for s in inactive_staffs:
            print(f"Xóa staff rác: {s.full_name} (ID: {s.id})")
            # Delete translations first (although cascade option is there, let's be explicit)
            await db.execute(delete(StaffTranslation).where(StaffTranslation.staff_id == s.id))
            await db.delete(s)
        await db.flush()

        # 2. Xóa các Positions rác
        # Các position rác là:
        # - Tên VI/EN chứa "No VI Name", "No EN Name"
        # - Hoặc duplicate "Giảng viên" (chỉ giữ lại ID 0f7b64a8-0f1a-4b88-a0f8-8935c4967d97 đang được dùng)
        # - Hoặc các chức danh cũ không còn sử dụng (Chủ tịch Công đoàn, Trưởng bộ môn, Phó bộ môn, Bí thư, Chuyên viên phòng viện...)
        stmt_pos = select(Position)
        positions = (await db.execute(stmt_pos)).scalars().all()
        
        valid_positions_vi = {"giảng viên", "giảng viên chính", "giảng viên cao cấp", "chuyên viên", "trợ giảng"}
        # We only keep the specific valid position ID for "Giảng viên" that has active staffs
        kept_giang_vien_id = "0f7b64a8-0f1a-4b88-a0f8-8935c4967d97"

        for p in positions:
            vi_name = next((t.name for t in p.translations if t.language.code == "vi"), "No VI Name")
            vi_name_clean = vi_name.lower().strip()
            
            should_delete = False
            reason = ""

            if "no vi name" in vi_name_clean:
                should_delete = True
                reason = "Tên trống (No VI Name)"
            elif vi_name_clean == "giảng viên" and str(p.id) != kept_giang_vien_id:
                should_delete = True
                reason = "Trùng lặp Giảng viên"
            elif vi_name_clean not in valid_positions_vi:
                should_delete = True
                reason = f"Chức danh cũ/không dùng ({vi_name})"

            if should_delete:
                print(f"Xóa position rác: {vi_name} | ID: {p.id} | Lý do: {reason}")
                await db.execute(delete(PositionTranslation).where(PositionTranslation.position_id == p.id))
                await db.delete(p)

        # 3. Xóa các Departments rác (Dept A, B, C, PCN...)
        stmt_dept = select(Department)
        departments = (await db.execute(stmt_dept)).scalars().all()
        
        valid_depts = {
            "ban lãnh đạo trường", "khoa công nghệ thông tin", 
            "khoa khoa học máy tính và trí tuệ nhân tạo", 
            "khoa công nghệ kỹ thuật điện", "khoa tự động hóa", 
            "khoa điện tử và công nghệ bán dẫn", 
            "khoa công nghệ kỹ thuật ô tô", "văn phòng trường"
        }

        for d in departments:
            vi_name = next((t.name for t in d.translations if t.language.code == "vi"), "No VI Name")
            vi_name_clean = vi_name.lower().strip()

            should_delete = False
            reason = ""

            if "no vi name" in vi_name_clean:
                should_delete = True
                reason = "Tên trống (No VI Name)"
            elif "dept" in vi_name_clean:
                should_delete = True
                reason = f"Tên test ({vi_name})"
            elif vi_name_clean not in valid_depts:
                should_delete = True
                reason = f"Phòng ban cũ/không dùng ({vi_name})"

            if should_delete:
                print(f"Xóa department rác: {vi_name} | ID: {d.id} | Lý do: {reason}")
                # We need to make sure menus or categories referencing it are updated.
                # In previous step, we already updated all menus to point to new department IDs.
                # Let's delete this department's translations and record.
                await db.execute(delete(DepartmentTranslation).where(DepartmentTranslation.department_id == d.id))
                await db.delete(d)

        # 4. Xóa Academic Titles rác (Ví dụ: "Giáo sư" nếu không được sử dụng)
        # Quyết định điều động không có Giáo sư nào, nhưng "Giáo sư" là một học hàm thật hợp lệ,
        # chỉ là chưa dùng. Ta nên giữ "Giáo sư" và "Phó giáo sư" vì đây là seed chuẩn.
        # Nên không xóa Academic Titles.

        # 5. Xóa Degrees rác
        # Bác sĩ, Tiến sĩ khoa học, Kỹ sư hiện tại không có active staff. Nhưng đó là các học vị thật hợp lệ.
        # Chúng ta chỉ xóa nếu có degree nào tên là "No VI Name" (không có).
        # Nên ta giữ nguyên Degrees chuẩn.

        await db.commit()
        print("Đã hoàn tất dọn dẹp dữ liệu rác thành công!")

if __name__ == "__main__":
    asyncio.run(main())
