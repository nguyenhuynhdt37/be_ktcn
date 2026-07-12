import asyncio
import uuid

# Import all models to prevent Mapper expression failures
from app.modules.language.models import *
from app.modules.category.models import *
from app.modules.audit.models import *
from app.modules.article.models import *
from app.modules.tag.models import *
from app.modules.department.models import *
from app.modules.position.models import *
from app.modules.staff.models import *
from app.modules.academic_title.models import *
from app.modules.degree.models import *
from app.modules.banner.models import *
from app.modules.ai_hub.models import *
from app.modules.statistics.models import *
from app.modules.consultation.models import *
from app.modules.notification.models import *
from app.modules.program.models import *
from app.modules.gallery.models import *

from sqlalchemy import select
from app.core.database import SessionLocal

async def seed_gallery():
    print("=== SEEDING EXQUISITE DEPARTMENT GALLERY FOR CS & AI ===")
    db = SessionLocal()
    try:
        dept_id = uuid.UUID("ad04f537-60de-473a-824c-ba8f17af1f1d")
        
        # 1. Kiểm tra sự tồn tại của Department
        dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalar_one_or_none()
        if not dept:
            print("Không tìm thấy Khoa CS&AI")
            return
            
        vi_lang = (await db.execute(select(Language).where(Language.code == "vi"))).scalar_one()
        en_lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        
        # 2. Xóa các gallery cũ của khoa này nếu có để seed mới sạch sẽ
        existing_galleries = (await db.execute(
            select(DepartmentGallery).where(DepartmentGallery.department_id == dept_id)
        )).scalars().all()
        for g in existing_galleries:
            await db.delete(g)
        await db.flush()
        
        # 3. Tạo album 1: Hoạt động học thuật và nghiên cứu
        gallery1 = DepartmentGallery(
            department_id=dept_id,
            cover_object_key="files/995259bd1e1945a7a4ee9500045b7df5", # IMG_2106.jpg
            sort_order=0,
            is_active=True,
            translations=[
                DepartmentGalleryTranslation(
                    language_id=vi_lang.id,
                    title="Hoạt động học thuật & Nghiên cứu khoa học",
                    description="Hình ảnh các buổi hội thảo quốc tế, seminar chuyên đề và giờ nghiên cứu của giảng viên, sinh viên khoa CS&AI."
                ),
                DepartmentGalleryTranslation(
                    language_id=en_lang.id,
                    title="Academic & Research Activities",
                    description="Photos from international conferences, academic seminars, and research sessions of CS&AI faculty and students."
                )
            ],
            items=[
                DepartmentGalleryItem(
                    media_item_id=uuid.UUID("11b12b45-e5dd-417f-a25f-2dc8aa23649a"),
                    caption="Hội thảo Quốc tế về Trí tuệ nhân tạo và Ứng dụng thực tiễn",
                    alt_text="Hội thảo AI",
                    sort_order=0,
                    is_active=True
                ),
                DepartmentGalleryItem(
                    media_item_id=uuid.UUID("cfbce4ec-589c-4226-894e-a053299145cd"),
                    caption="Sinh viên bảo vệ đề tài Nghiên cứu khoa học xuất sắc cấp Trường",
                    alt_text="Bảo vệ đề tài",
                    sort_order=1,
                    is_active=True
                ),
                DepartmentGalleryItem(
                    media_item_id=uuid.UUID("79169d72-cd7b-4035-ba2d-35c565da8858"),
                    caption="Buổi Seminar nghiên cứu định kỳ của Nhóm Học sâu và NLP",
                    alt_text="Seminar Deep Learning",
                    sort_order=2,
                    is_active=True
                )
            ]
        )
        db.add(gallery1)
        
        # 4. Tạo album 2: Cơ sở vật chất phòng Lab hiện đại
        gallery2 = DepartmentGallery(
            department_id=dept_id,
            cover_object_key="files/71aedb275825416aa7c287ff0e5e51ab", # IMG_2106.jpg
            sort_order=1,
            is_active=True,
            translations=[
                DepartmentGalleryTranslation(
                    language_id=vi_lang.id,
                    title="Hệ thống phòng nghiên cứu & Key Laboratories",
                    description="Khám phá không gian thực hành, hệ thống máy chủ GPU hiệu năng cao phục vụ huấn luyện các mô hình AI tiên tiến."
                ),
                DepartmentGalleryTranslation(
                    language_id=en_lang.id,
                    title="Modern Facilities & Laboratories",
                    description="Explore our research spaces and high-performance GPU server clusters dedicated to training advanced AI models."
                )
            ],
            items=[
                DepartmentGalleryItem(
                    media_item_id=uuid.UUID("acdfe54c-5563-48bd-bed8-23fd36485298"),
                    caption="Không gian làm việc chung của Lab Nghiên cứu Tương tác Người - Máy",
                    alt_text="HCI Lab",
                    sort_order=0,
                    is_active=True
                ),
                DepartmentGalleryItem(
                    media_item_id=uuid.UUID("81238401-6cd4-467d-a376-e6ee7677b3f7"),
                    caption="Hệ thống siêu máy tính máy chủ GPU phục vụ dự án nhận diện y tế",
                    alt_text="AI Server Cluster",
                    sort_order=1,
                    is_active=True
                )
            ]
        )
        db.add(gallery2)
        
        await db.commit()
        print("Tạo thư viện ảnh (Galleries) mẫu thành công rực rỡ cho Khoa CS&AI!")
    except Exception as e:
        await db.rollback()
        print(f"Lỗi: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(seed_gallery())
