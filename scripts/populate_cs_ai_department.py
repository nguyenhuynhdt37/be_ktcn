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

from sqlalchemy import select, update
from app.core.database import SessionLocal

async def populate_data():
    print("=== POPULATE EXQUISITE CS & AI DEPARTMENT DATA ===")
    db = SessionLocal()
    try:
        dept_id = uuid.UUID("ad04f537-60de-473a-824c-ba8f17af1f1d")
        
        # 1. Kiểm tra sự tồn tại của Department
        stmt = select(Department).where(Department.id == dept_id)
        res = await db.execute(stmt)
        dept = res.scalar_one_or_none()
        if not dept:
            print(f"Lỗi: Không tìm thấy bộ môn với ID {dept_id}")
            return
        
        # 2. Lấy ngôn ngữ vi và en
        vi_lang = (await db.execute(select(Language).where(Language.code == "vi"))).scalar_one()
        en_lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        
        # 3. Cập nhật các trường cơ bản của Department
        dept.code = "FCSAI"
        dept.unit_type = "faculty"
        dept.logo_object_key = "logos/cs-ai-logo.png"
        dept.banner_object_key = "banners/cs-ai-banner.png"
        dept.phone = "+84 (24) 3754 7890"
        dept.email = "cs.ai@university.edu.vn"
        dept.website = "https://cs-ai.university.edu.vn"
        dept.office = "Tầng 5, Tòa nhà C2, Khu Đô thị Đại học"
        dept.head_staff_id = uuid.UUID("43395772-c785-4e9a-ba17-8fabe8599ca1") # Phan Anh Phong
        
        # 4. Xử lý bản dịch tiếng Việt
        vi_trans = (await db.execute(
            select(DepartmentTranslation).where(
                DepartmentTranslation.department_id == dept_id,
                DepartmentTranslation.language_id == vi_lang.id
            )
        )).scalar_one_or_none()
        
        vi_mission = """<h3>Sứ mệnh của Khoa Khoa học máy tính và Trí tuệ nhân tạo</h3>
<p>Chúng tôi cam kết cung cấp môi trường giáo dục tiên tiến, thúc đẩy sự sáng tạo và nghiên cứu đỉnh cao trong lĩnh vực khoa học máy tính và trí tuệ nhân tạo. Sứ mệnh của khoa bao gồm:</p>
<ul>
    <li><strong>Đào tạo xuất sắc:</strong> Cung cấp chương trình đào tạo đạt chuẩn quốc tế, giúp sinh viên phát triển tư duy phản biện, kỹ năng giải quyết vấn đề và năng lực nghiên cứu khoa học.</li>
    <li><strong>Nghiên cứu sáng tạo:</strong> Thực hiện các nghiên cứu tiên phong, ứng dụng AI để giải quyết các thách thức lớn của xã hội, kinh tế và môi trường.</li>
    <li><strong>Hợp tác phát triển:</strong> Xây dựng mối quan hệ đối tác chiến lược với các doanh nghiệp công nghệ hàng đầu toàn cầu và các tổ chức nghiên cứu uy tín quốc tế.</li>
</ul>"""

        vi_vision = """<h3>Tầm nhìn phát triển đến năm 2035</h3>
<p>Trở thành khoa nghiên cứu và đào tạo hàng đầu trong khu vực Đông Nam Á về Khoa học máy tính và Trí tuệ nhân tạo, là nơi hội tụ các nhà khoa học xuất sắc, các sinh viên ưu tú và đối tác công nghệ chiến lược toàn cầu.</p>"""

        vi_history = """<h3>Lịch sử hình thành và phát triển</h3>
<p>Được thành lập từ việc nâng cấp Bộ môn Khoa học máy tính và Trung tâm Nghiên cứu AI tiên tiến, khoa đã nhanh chóng khẳng định vị trí dẫn đầu của mình tại trường:</p>
<ul>
    <li><strong>2015:</strong> Thành lập nhóm nghiên cứu Trí tuệ nhân tạo đầu tiên của trường.</li>
    <li><strong>2018:</strong> Ra mắt chuyên ngành đào tạo Trí tuệ nhân tạo bậc Đại học chính quy đầu tiên.</li>
    <li><strong>2022:</strong> Chính thức thành lập Khoa Khoa học máy tính và Trí tuệ nhân tạo để đáp ứng nhu cầu nhân lực chất lượng cao của kỷ nguyên số.</li>
</ul>"""

        vi_research = """<h3>Các hướng nghiên cứu mũi nhọn</h3>
<p>Khoa tập trung nguồn lực vào các lĩnh vực nghiên cứu hiện đại mang tính thực tiễn cao:</p>
<ol>
    <li><strong>Trí tuệ nhân tạo (AI) & Học máy (Machine Learning):</strong> Phát triển thuật toán học sâu, mô hình ngôn ngữ lớn (LLMs), học tăng cường.</li>
    <li><strong>Xử lý ngôn ngữ tự nhiên (NLP):</strong> Nghiên cứu công nghệ giọng nói và dịch thuật tự động cho tiếng Việt và các ngôn ngữ khu vực.</li>
    <li><strong>Thị giác máy tính (Computer Vision):</strong> Ứng dụng nhận dạng khuôn mặt, phân tích hình ảnh y tế, xe tự hành.</li>
    <li><strong>Khoa học dữ liệu (Data Science):</strong> Phân tích dữ liệu lớn (Big Data), khai phá tri thức ứng dụng trong tài chính và y tế.</li>
</ol>"""

        if not vi_trans:
            vi_trans = DepartmentTranslation(
                department_id=dept_id,
                language_id=vi_lang.id,
                name="Khoa Khoa học máy tính và Trí tuệ nhân tạo",
                description="Khoa Khoa học máy tính và Trí tuệ nhân tạo (CS&AI) là trung tâm đào tạo và nghiên cứu hàng đầu về công nghệ số.",
                mission=vi_mission,
                vision=vi_vision,
                history=vi_history,
                research_overview=vi_research,
                seo_title="Khoa Khoa học máy tính và Trí tuệ nhân tạo (CS & AI)",
                seo_description="Trang chủ Khoa Khoa học máy tính và Trí tuệ nhân tạo. Thông tin chi tiết về chương trình đào tạo, hướng nghiên cứu, cơ sở vật chất và giảng viên.",
                slug="khoa-khoa-hoc-may-tinh-va-tri-tue-nhan-tao"
            )
            db.add(vi_trans)
        else:
            vi_trans.name = "Khoa Khoa học máy tính và Trí tuệ nhân tạo"
            vi_trans.description = "Khoa Khoa học máy tính và Trí tuệ nhân tạo (CS&AI) là trung tâm đào tạo và nghiên cứu hàng đầu về công nghệ số."
            vi_trans.mission = vi_mission
            vi_trans.vision = vi_vision
            vi_trans.history = vi_history
            vi_trans.research_overview = vi_research
            vi_trans.seo_title = "Khoa Khoa học máy tính và Trí tuệ nhân tạo (CS & AI)"
            vi_trans.seo_description = "Trang chủ Khoa Khoa học máy tính và Trí tuệ nhân tạo. Thông tin chi tiết về chương trình đào tạo, hướng nghiên cứu, cơ sở vật chất và giảng viên."
            vi_trans.slug = "khoa-khoa-hoc-may-tinh-va-tri-tue-nhan-tao"
            db.add(vi_trans)

        # 5. Xử lý bản dịch tiếng Anh
        en_trans = (await db.execute(
            select(DepartmentTranslation).where(
                DepartmentTranslation.department_id == dept_id,
                DepartmentTranslation.language_id == en_lang.id
            )
        )).scalar_one_or_none()

        en_mission = """<h3>Mission of the Faculty of CS & AI</h3>
<p>We are dedicated to providing a cutting-edge education, fostering breakthrough research in computer science and artificial intelligence. Our mission encompasses:</p>
<ul>
    <li><strong>Educational Excellence:</strong> Delivering international standard curriculums that foster critical thinking, problem-solving, and scientific research capabilities.</li>
    <li><strong>Innovative Research:</strong> Conducting pioneering research and applying AI to address grand challenges in society, economy, and environment.</li>
    <li><strong>Global Collaboration:</strong> Establishing strategic partnerships with top tech corporations and world-class research institutes.</li>
</ul>"""

        en_vision = """<h3>Vision Towards 2035</h3>
<p>To become a leading research and educational institution in Southeast Asia for Computer Science and Artificial Intelligence, serving as a hub for outstanding scientists, brilliant students, and global strategic technology partners.</p>"""

        en_history = """<h3>Milestones & History</h3>
<p>Originating from the Department of Computer Science and the Advanced AI Research Lab, the faculty quickly grew into a leading force:</p>
<ul>
    <li><strong>2015:</strong> Formed the first AI research group at the university.</li>
    <li><strong>2018:</strong> Launched the first formal undergraduate program in Artificial Intelligence.</li>
    <li><strong>2022:</strong> Officially established the Faculty of Computer Science and Artificial Intelligence to meet the soaring demand for digital talents.</li>
</ul>"""

        en_research = """<h3>Key Research Directions</h3>
<p>Our faculty focuses on highly practical and modern research fields:</p>
<ol>
    <li><strong>Artificial Intelligence & Machine Learning:</strong> Deep learning architectures, LLMs, reinforcement learning.</li>
    <li><strong>Natural Language Processing (NLP):</strong> Speech technology and machine translation tailored for Vietnamese and regional languages.</li>
    <li><strong>Computer Vision:</strong> Facial recognition, medical image analysis, autonomous systems.</li>
    <li><strong>Data Science & Big Data:</strong> Analyzing large-scale datasets, knowledge discovery applied in finance and healthcare.</li>
</ol>"""

        if not en_trans:
            en_trans = DepartmentTranslation(
                department_id=dept_id,
                language_id=en_lang.id,
                name="Faculty of Computer Science and Artificial Intelligence",
                description="The Faculty of Computer Science and Artificial Intelligence (CS&AI) is a leading center for education and research in digital technology.",
                mission=en_mission,
                vision=en_vision,
                history=en_history,
                research_overview=en_research,
                seo_title="Faculty of Computer Science and Artificial Intelligence (CS & AI)",
                seo_description="Official website of the Faculty of Computer Science and Artificial Intelligence. Learn more about our academic programs, research directions, faculty members, and campus facilities.",
                slug="faculty-of-computer-science-and-artificial-intelligence"
            )
            db.add(en_trans)
        else:
            en_trans.name = "Faculty of Computer Science and Artificial Intelligence"
            en_trans.description = "The Faculty of Computer Science and Artificial Intelligence (CS&AI) is a leading center for education and research in digital technology."
            en_trans.mission = en_mission
            en_trans.vision = en_vision
            en_trans.history = en_history
            en_trans.research_overview = en_research
            en_trans.seo_title = "Faculty of Computer Science and Artificial Intelligence (CS & AI)"
            en_trans.seo_description = "Official website of the Faculty of Computer Science and Artificial Intelligence. Learn more about our academic programs, research directions, faculty members, and campus facilities."
            en_trans.slug = "faculty-of-computer-science-and-artificial-intelligence"
            db.add(en_trans)
            
        await db.commit()
        print("Cập nhật dữ liệu Khoa CS&AI hoàn thành xuất sắc!")
    except Exception as e:
        await db.rollback()
        print(f"Lỗi xảy ra: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(populate_data())
