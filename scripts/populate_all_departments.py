import asyncio
import uuid
from datetime import datetime, UTC

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

DEPARTMENTS_DATA = {
    # 1. Khoa Công nghệ thông tin
    "05597b7e-5999-482a-86f7-363937b1e4de": {
        "code": "FIT",
        "unit_type": "faculty",
        "logo_object_key": "logos/fit-logo.png",
        "banner_object_key": "banners/fit-banner.png",
        "phone": "+84 (24) 3754 7891",
        "email": "fit@university.edu.vn",
        "website": "https://fit.university.edu.vn",
        "office": "Tầng 3, Tòa nhà C1, Khu Đô thị Đại học",
        "head_staff_id": "36b6a12f-560b-44c2-a660-d819004b2929", # Đặng Hồng Lĩnh
        "vi": {
            "name": "Khoa Công nghệ thông tin",
            "description": "Khoa Công nghệ thông tin (FIT) là một trong những khoa đầu ngành, đi đầu trong đào tạo nhân lực CNTT chất lượng cao.",
            "mission": "<p>Đào tạo nguồn nhân lực chất lượng cao, có khả năng thích ứng với sự thay đổi nhanh chóng của công nghệ. Khoa tập trung trang bị cho sinh viên nền tảng toán học vững chắc, tư duy thuật toán chuyên sâu và kỹ năng thực hành xuất sắc trong lĩnh vực phát triển phần mềm, trí tuệ nhân tạo và an toàn thông tin.</p><p>Bên cạnh đào tạo, khoa định hướng trở thành trung tâm nghiên cứu khoa học công nghệ mũi nhọn, chuyển giao tri thức trực tiếp cho các doanh nghiệp CNTT hàng đầu và tư vấn chính sách công nghệ cho các cơ quan nhà nước.</p>",
            "vision": "<p>Trở thành một trong những khoa Công nghệ thông tin hàng đầu tại Việt Nam và đạt uy tín cao trong khu vực Đông Nam Á về chất lượng giảng dạy, nghiên cứu khoa học. Đến năm 2030, tất cả các chương trình đào tạo của khoa đều đạt chuẩn kiểm định quốc tế ABET, mở ra cơ hội làm việc toàn cầu cho sinh viên tốt nghiệp.</p>",
            "history": "<p>Tiền thân là Bộ môn Tin học thuộc Khoa Cơ bản, được chính thức nâng cấp thành Khoa Công nghệ thông tin từ năm 1995 nhằm đáp ứng nhu cầu nhân lực công nghệ thông tin trong thời kỳ công nghiệp hóa, hiện đại hóa đất nước.</p><p>Trải qua hơn 30 năm xây dựng và phát triển, Khoa đã đạt được nhiều huân chương lao động và bằng khen của Chính phủ nhờ những đóng góp vượt bậc trong sự nghiệp giáo dục. Hiện nay, khoa sở hữu hệ thống các phòng lab hiện đại cùng đội ngũ giảng viên gồm 100% có trình độ sau đại học, trong đó hơn 50% là Tiến sĩ tốt nghiệp từ các nước phát triển.</p>",
            "research_overview": "<p>Các hoạt động nghiên cứu khoa học của khoa được tổ chức bài bản thông qua 4 nhóm nghiên cứu trọng điểm:</p><ul><li><strong>Nhóm nghiên cứu An toàn thông tin:</strong> Tập trung vào mật mã học, bảo mật hệ điều hành và phát hiện mã độc bằng AI.</li><li><strong>Nhóm công nghệ tri thức và dữ liệu:</strong> Khai phá dữ liệu lớn, tối ưu hóa công cụ tìm kiếm và phân tích mạng xã hội.</li><li><strong>Nhóm Kỹ thuật phần mềm:</strong> Nghiên cứu quy trình phát triển Agile, kiến trúc microservices và kiểm thử tự động hệ thống nhúng.</li><li><strong>Nhóm Mạng máy tính và IoT:</strong> Thiết kế kiến trúc mạng 5G/6G, định tuyến tối ưu trong các hệ thống cảm biến không dây.</li></ul>",
            "seo_title": "Khoa Công nghệ thông tin - Trường Đại học Kỹ thuật Công nghệ",
            "seo_description": "Trang chủ Khoa Công nghệ thông tin. Cung cấp thông tin chương trình giảng dạy, nghiên cứu khoa học và kết nối doanh nghiệp.",
            "slug": "khoa-cong-nghe-thong-tin"
        },
        "en": {
            "name": "Faculty of Information Technology",
            "description": "The Faculty of Information Technology (FIT) is a premier institution in IT education, driving digital transformation.",
            "mission": "<p>Educating high-quality IT professionals adaptive to rapid technological changes. The faculty focuses on solid mathematical foundations, advanced algorithmic thinking, and hand-on engineering skills in software development, AI, and information security.</p>",
            "vision": "<p>To be a leading IT faculty in Vietnam and highly reputable in ASEAN. By 2030, all academic curricula will be accredited under international ABET standards, opening global career paths for graduates.</p>",
            "history": "<p>Originating from the Computer Science Department under the Faculty of Basic Sciences, FIT was officially founded in 1995. Over three decades of growth, it has evolved into a prominent center for advanced IT education and ODA-backed research labs.</p>",
            "research_overview": "<p>Our faculty coordinates active research across four core focus areas:</p><ul><li><strong>Cybersecurity:</strong> Cryptography, OS security, and AI-driven malware detection.</li><li><strong>Data & Knowledge Engineering:</strong> Big data mining, semantic search, and social network analysis.</li><li><strong>Software Engineering:</strong> Agile processes, microservices architecture, and test automation.</li><li><strong>Computer Networks & IoT:</strong> 5G/6G architectures and routing algorithms for wireless sensor networks.</li></ul>",
            "seo_title": "Faculty of Information Technology - Tech University",
            "seo_description": "Official homepage of the Faculty of Information Technology, providing insights into curriculum, academic events, and industry relationships.",
            "slug": "faculty-of-information-technology"
        }
    },
    # 2. Khoa Công nghệ kỹ thuật Điện
    "8462b8f3-d85e-4308-a2df-ffa87b87fb15": {
        "code": "FEE",
        "unit_type": "faculty",
        "logo_object_key": "logos/fee-logo.png",
        "banner_object_key": "banners/fee-banner.png",
        "phone": "+84 (24) 3754 7892",
        "email": "fee@university.edu.vn",
        "website": "https://fee.university.edu.vn",
        "office": "Tầng 2, Tòa nhà C3, Khu Đô thị Đại học",
        "head_staff_id": "b520734a-48b0-4ac3-a74b-ad3ae8563811", # Phạm Hoàng Nam
        "vi": {
            "name": "Khoa Công nghệ kỹ thuật Điện",
            "description": "Khoa Điện đào tạo các kỹ sư thiết kế, vận hành hệ thống điện thông minh, năng lượng tái tạo và điện dân dụng.",
            "mission": "<p>Đóng vai trò then chốt trong việc đào tạo các thế hệ kỹ sư kỹ thuật điện có kiến thức chuyên môn sâu, kỹ năng thực hành thành thạo và đạo đức nghề nghiệp vững vàng. Khoa cam kết cung cấp giải pháp, công nghệ tiên tiến phục vụ quá trình truyền tải, phân phối điện năng và ứng dụng năng lượng sạch.</p>",
            "vision": "<p>Hướng tới xây dựng khoa Điện hiện đại, gắn liền đào tạo lý thuyết với thực tế sản xuất tại các nhà máy, tập đoàn năng lượng lớn. Khoa phấn đấu trở thành đơn vị đi đầu cả nước về chuyển giao công nghệ điện thông minh (Smart Grid) và tích hợp các nguồn năng lượng tái tạo vào lưới điện quốc gia.</p>",
            "history": "<p>Được thành lập từ năm 2000, bắt đầu với quy mô đào tạo nhỏ. Trải qua chặng đường phát triển liên tục, khoa đã nâng cấp toàn diện cơ sở vật chất từ nguồn vốn ODA và các dự án hợp tác quốc tế, trang bị các phòng thí nghiệm mô phỏng hệ thống điện thời gian thực đạt tiêu chuẩn châu Âu.</p>",
            "research_overview": "<p>Đội ngũ nghiên cứu của khoa tập trung vào các giải pháp năng lượng bền vững:</p><ul><li><strong>Hệ thống điện thông minh (Smart Grid):</strong> Điều khiển tự động lưới điện phân phối, tối ưu hóa lưu lượng công suất.</li><li><strong>Năng lượng tái tạo:</strong> Giải pháp tích hợp điện mặt trời mái nhà và tua-bin gió vào lưới điện yếu.</li><li><strong>Hệ thống lưu trữ năng lượng:</strong> Nghiên cứu pin lưu trữ dung lượng lớn và hệ thống quản lý pin thông minh (BMS).</li></ul>",
            "seo_title": "Khoa Công nghệ kỹ thuật Điện - Đào tạo kỹ sư điện thông minh",
            "seo_description": "Trang thông tin của Khoa Công nghệ kỹ thuật Điện. Đào tạo kỹ sư vận hành hệ thống năng lượng tái tạo, lưới điện hiện đại.",
            "slug": "khoa-cong-nghe-ky-thuat-dien"
        },
        "en": {
            "name": "Faculty of Electrical Engineering",
            "description": "We train engineers to design and operate smart grid systems, renewable energy, and power networks.",
            "mission": "<p>To nurture highly skilled and ethical electrical engineers. The faculty provides advanced technology solutions for electric power transmission, smart grids, and clean energy integration.</p>",
            "vision": "<p>To establish a modern engineering environment closely aligned with industrial giants. We aim to lead the nation in Smart Grid technology and integration of distributed renewable resources.</p>",
            "history": "<p>Established in 2000 with modest origins. Through continuous development, FEE has modernized its experimental facilities using ODA funding, installing real-time power system simulators matching European standards.</p>",
            "research_overview": "<p>FEE research groups focus on sustainable grid and device technologies:</p><ul><li><strong>Smart Grids:</strong> Automation of distribution systems and volt-var optimization.</li><li><strong>Renewable Integration:</strong> Rooftop solar PV and wind turbine stabilization.</li><li><strong>Energy Storage:</strong> High-capacity batteries and battery management systems (BMS).</li></ul>",
            "seo_title": "Faculty of Electrical Engineering - Smart Power Education",
            "seo_description": "Faculty of Electrical Engineering. Learn about renewable energy grid design, academic events, and professional career paths.",
            "slug": "faculty-of-electrical-engineering"
        }
    },
    # 3. Khoa Công nghệ kỹ thuật Ô tô
    "d4ed0343-ebfc-4f7f-9b6a-b4915123648e": {
        "code": "FAE",
        "unit_type": "faculty",
        "logo_object_key": "logos/fae-logo.png",
        "banner_object_key": "banners/fae-banner.png",
        "phone": "+84 (24) 3754 7893",
        "email": "fae@university.edu.vn",
        "website": "https://fae.university.edu.vn",
        "office": "Tầng 1, Tòa nhà Xưởng Thực hành cơ khí",
        "head_staff_id": "31152556-af7f-4e7d-a88b-ef1db7af6e2e", # Nguyễn Phúc Ngọc
        "vi": {
            "name": "Khoa Công nghệ kỹ thuật Ô tô",
            "description": "Khoa Ô tô tập trung vào đào tạo chế tạo ô tô, động cơ đốt trong và công nghệ xe điện, xe tự hành hiện đại.",
            "mission": "<p>Trang bị cho người học năng lực làm chủ công nghệ thiết kế, chế tạo, kiểm định và bảo dưỡng các loại phương tiện giao thông đường bộ. Chúng tôi chú trọng đào tạo thực hành thực tế, rèn luyện tư duy kỹ thuật và tính kỷ luật công nghiệp cao.</p>",
            "vision": "<p>Trở thành cơ sở đào tạo và nghiên cứu kỹ thuật ô tô hàng đầu khu vực, đạt chuẩn kiểm định chất lượng quốc gia và khu vực. Khoa định hướng phát triển mạnh mẽ mảng công nghệ xe điện (EV) và xe tự hành để bắt kịp xu thế giao thông xanh toàn cầu.</p>",
            "history": "<p>Thành lập nhằm đáp ứng sự phát triển bùng nổ của ngành công nghiệp ô tô tại Việt Nam. Khoa đã ký kết hợp tác chiến lược dài hạn với các tập đoàn sản xuất ô tô lớn trong và ngoài nước (như VinFast, Toyota, Thaco) mang lại cơ hội thực tập và việc làm trực tiếp cho 100% sinh viên tốt nghiệp.</p>",
            "research_overview": "<p>Các hướng nghiên cứu mũi nhọn của khoa bao gồm:</p><ul><li><strong>Công nghệ xe điện:</strong> Quản lý nhiệt độ khối pin, động cơ điện hiệu năng cao và hệ thống phanh tái sinh năng lượng.</li><li><strong>Hệ thống tự lái và ADAS:</strong> Phát triển thuật toán nhận diện làn đường, tránh va chạm sử dụng cảm biến LiDAR và Camera hành trình.</li><li><strong>Chẩn đoán lỗi thông minh:</strong> Ứng dụng AI phân tích tín hiệu âm thanh và rung động để phát hiện sớm các hư hỏng cơ khí.</li></ul>",
            "seo_title": "Khoa Công nghệ kỹ thuật Ô tô - Công nghệ xe điện tương lai",
            "seo_description": "Trang chủ Khoa Công nghệ kỹ thuật Ô tô. Đào tạo thiết kế, sửa chữa, bảo dưỡng ô tô thế hệ mới, xe tự hành, xe điện.",
            "slug": "khoa-cong-nghe-ky-thuat-o-to"
        },
        "en": {
            "name": "Faculty of Automotive Engineering",
            "description": "Focusing on automotive design, combustion engines, electric vehicles, and autonomous vehicle technologies.",
            "mission": "<p>Equipping students with capabilities to master road vehicle design, manufacturing, inspection, and maintenance. We emphasize real-world workshop practice, engineering logic, and industrial safety discipline.</p>",
            "vision": "<p>To be the premier institute for automotive engineering in the region. The faculty focuses on electric vehicles (EV) and self-driving technologies to align with global green transit initiatives.</p>",
            "history": "<p>Founded to fulfill the booming domestic automotive industry demand. FAE has established long-term strategic relationships with leading local and international manufacturers (including VinFast, Toyota, and Thaco).</p>",
            "research_overview": "<p>Key research directions include:</p><ul><li><strong>EV Technology:</strong> Battery pack thermal management, high-performance traction motors, and regenerative braking.</li><li><strong>Autonomous Systems & ADAS:</strong> Lane detection algorithms and collision avoidance using LiDAR and camera fusion.</li><li><strong>Intelligent Diagnostics:</strong> AI-powered vibration and audio signature analysis for predictive mechanical maintenance.</li></ul>",
            "seo_title": "Faculty of Automotive Engineering - Electric & Autonomous Vehicles",
            "seo_description": "Faculty of Automotive Engineering. Explore electric vehicle design courses, internships, and advanced mechanical workshops.",
            "slug": "faculty-of-automotive-engineering"
        }
    },
    # 4. Khoa Tự động hóa
    "17bea2af-23bb-4a80-9e28-27df6ec025c8": {
        "code": "FA",
        "unit_type": "faculty",
        "logo_object_key": "logos/fa-logo.png",
        "banner_object_key": "banners/fa-banner.png",
        "phone": "+84 (24) 3754 7894",
        "email": "fa@university.edu.vn",
        "website": "https://fa.university.edu.vn",
        "office": "Tầng 4, Tòa nhà C2, Khu Đô thị Đại học",
        "head_staff_id": "370f1f6c-ca30-4ad1-88e4-5831ec14ffff", # Tạ Hùng Cường
        "vi": {
            "name": "Khoa Tự động hóa",
            "description": "Khoa Tự động hóa (Control & Automation) trang bị kiến thức về robot học, hệ thống sản xuất tích hợp máy tính và IoT.",
            "mission": "<p>Đào tạo nguồn nhân lực chất lượng cao có khả năng thiết kế, vận hành các hệ thống điều khiển tự động và dây chuyền sản xuất thông minh. Khoa thúc đẩy hoạt động sáng tạo công nghệ, ứng dụng tự động hóa nâng cao năng suất lao động và giải phóng sức lao động con người.</p>",
            "vision": "<p>Trở thành trung tâm đào tạo, nghiên cứu khoa học và chuyển giao công nghệ hàng đầu về điều khiển tự động và robot thông minh trong cả nước. Khoa hướng tới kiểm định chất lượng theo tiêu chuẩn mạng lưới các trường đại học Đông Nam Á (AUN-QA).</p>",
            "history": "<p>Trải qua nhiều giai đoạn phát triển từ bộ môn điều khiển tự động hóa thuộc khoa Điện, khoa Tự động hóa chính thức được thành lập riêng biệt để đáp ứng cuộc cách mạng công nghiệp lần thứ tư, trở thành địa chỉ tin cậy hàng đầu của các doanh nghiệp FDI.</p>",
            "research_overview": "<p>Các đề tài nghiên cứu trọng điểm của khoa gồm:</p><ul><li><strong>Robotics & Cơ điện tử:</strong> Phát triển robot cộng tác (Cobot), cánh tay robot công nghiệp độ chính xác cao và robot y tế.</li><li><strong>Hệ thống điều khiển phân tán (DCS) & SCADA:</strong> Giám sát trực quan hóa thời gian thực các dây chuyền sản xuất bia, xi măng và xử lý nước thải.</li><li><strong>Ứng dụng Trí tuệ nhân tạo (AI):</strong> Điều khiển thông minh thích nghi tối ưu hóa các hệ thống phi tuyến phức tạp.</li></ul>",
            "seo_title": "Khoa Tự động hóa - Kỹ thuật Điều khiển và Tự động hóa",
            "seo_description": "Trang chủ Khoa Tự động hóa. Đào tạo chuyên sâu Robot học, Lập trình PLC, Vi điều khiển và IoT công nghiệp.",
            "slug": "khoa-tu-dong-hoa"
        },
        "en": {
            "name": "Faculty of Automation",
            "description": "Providing expertise in Robotics, Computer-Integrated Manufacturing, and Industrial IoT.",
            "mission": "<p>To produce quality control and automation engineers who design smart industrial lines. We foster tech innovation that raises productivity and improves safety in physical labor.</p>",
            "vision": "<p>To be the leading national training and technology transfer center for adaptive control and robotics, aligned under the AUN-QA framework.</p>",
            "history": "<p>Developed from the automatic control division of the Electrical Faculty. FA was established to address Industry 4.0 trends and serves as a key partner for global manufacturing enterprises.</p>",
            "research_overview": "<p>Major research initiatives focus on:</p><ul><li><strong>Robotics & Mechatronics:</strong> Collaborative robots (Cobots), high-precision actuators, and surgical assistive devices.</li><li><strong>DCS & SCADA Systems:</strong> Real-time visualization and remote telemetry for manufacturing plants.</li><li><strong>Intelligent AI Control:</strong> Adaptive neuro-fuzzy controllers optimized for complex non-linear setups.</li></ul>",
            "seo_title": "Faculty of Automation - Control and Automation Engineering",
            "seo_description": "Faculty of Automation. Learn PLC programming, robotics engineering, SCADA integration, and Industrial IoT.",
            "slug": "faculty-of-automation"
        }
    },
    # 5. Khoa Điện tử và Công nghệ bán dẫn
    "363a4f61-df54-49bb-a0aa-d14fd825af9f": {
        "code": "FESD",
        "unit_type": "faculty",
        "logo_object_key": "logos/fesd-logo.png",
        "banner_object_key": "banners/fesd-banner.png",
        "phone": "+84 (24) 3754 7895",
        "email": "fesd@university.edu.vn",
        "website": "https://fesd.university.edu.vn",
        "office": "Tầng 6, Tòa nhà C2, Khu Đô thị Đại học",
        "head_staff_id": "54dccd28-9bec-43f5-8e78-4bf15e430026", # Đặng Thái Sơn
        "vi": {
            "name": "Khoa Điện tử và Công nghệ bán dẫn",
            "description": "Khoa đi đầu trong nghiên cứu vi mạch, thiết kế chíp bán dẫn và các vi hệ thống điện tử tiên tiến.",
            "mission": "<p>Thực hiện sứ mệnh quốc gia về đào tạo nguồn nhân lực chất lượng cao trong ngành công nghiệp thiết kế vi mạch và công nghệ bán dẫn. Khoa cam kết đi đầu trong chuyển giao tri thức thiết kế chíp, xây dựng chuỗi cung ứng công nghệ cao vững mạnh.</p>",
            "vision": "<p>Trở thành trung tâm đào tạo vi mạch bán dẫn hàng đầu Việt Nam và là đối tác đào tạo, R&D tin cậy của các tập đoàn bán dẫn đa quốc gia hàng đầu thế giới (như Synopsys, Cadence, Intel).</p>",
            "history": "<p>Được thành lập trong bối cảnh toàn cầu và quốc gia đẩy mạnh phát triển chuỗi cung ứng bán dẫn. Khoa được đầu tư đồng bộ hệ thống bản quyền phần mềm thiết kế chíp chính hãng và phòng sạch thực hành chế tạo linh kiện quy mô bán công nghiệp.</p>",
            "research_overview": "<p>Các hoạt động nghiên cứu khoa học cốt lõi:</p><ul><li><strong>Thiết kế vi mạch tích hợp (IC Design):</strong> Thiết kế chip tín hiệu hỗn hợp, bộ vi xử lý nhúng RISC-V công suất thấp.</li><li><strong>Linh kiện bán dẫn MEMS:</strong> Cảm biến áp suất, cảm biến gia tốc ứng dụng trong thiết bị thông minh.</li><li><strong>Đóng gói và kiểm thử chip:</strong> Tối ưu hóa tản nhiệt vi mạch, kiểm tra độ tin cậy và phát hiện lỗi vật lý trên silicon.</li></ul>",
            "seo_title": "Khoa Điện tử và Công nghệ bán dẫn - Đào tạo thiết kế chíp",
            "seo_description": "Trang thông tin Khoa Điện tử và Công nghệ bán dẫn. Đào tạo thiết kế vi mạch IC, công nghệ chế tạo bán dẫn hàng đầu.",
            "slug": "khoa-dien-tu-va-cong-nghe-ban-dan"
        },
        "en": {
            "name": "Faculty of Electronics and Semiconductor Technology",
            "description": "Leading the nation in microchip research, semiconductor design, and advanced electronic microsystems.",
            "mission": "<p>To carry out the national mission of developing skilled talents for the semiconductor industry. FESD is committed to chip design education and building cleanroom-level R&D competencies.</p>",
            "vision": "<p>To establish a leading microelectronics hub in Vietnam, partnering with global EDA leaders (such as Synopsys, Cadence) and fabrication foundries.</p>",
            "history": "<p>Founded in response to global semiconductor supply chain shifts. The faculty is equipped with fully licensed EDA design software suites and pilot-line cleanroom equipment for semiconductor microfabrication.</p>",
            "research_overview": "<p>Key R&D areas include:</p><ul><li><strong>IC Design:</strong> Mixed-signal chip architectures and ultra-low-power RISC-V embedded processors.</li><li><strong>MEMS Devices:</strong> Micro-sensors and micro-actuators integrated into IoT devices.</li><li><strong>Accreditation & Packaging:</strong> Thermal management of silicon chips and hardware security testing.</li></ul>",
            "seo_title": "Faculty of Electronics and Semiconductor Technology - IC Design Programs",
            "seo_description": "Faculty of Electronics and Semiconductor Technology. Learn IC design, cleanroom chip testing, and device engineering.",
            "slug": "faculty-of-electronics-and-semiconductor-technology"
        }
    },
    # 6. Văn phòng Trường
    "42ad4b7a-96e7-4e5a-a97b-ae581d0684cd": {
        "code": "OAS",
        "unit_type": "office",
        "logo_object_key": "logos/oas-logo.png",
        "banner_object_key": "banners/oas-banner.png",
        "phone": "+84 (24) 3754 7896",
        "email": "office@university.edu.vn",
        "website": "https://office.university.edu.vn",
        "office": "Tầng 1, Tòa nhà Hiệu bộ",
        "head_staff_id": "8a5b88c1-24e8-4618-a770-bc1402d4f12b", # Hoàng Cẩm Nhung
        "vi": {
            "name": "Văn phòng Trường",
            "description": "Đơn vị tham mưu, tổng hợp và giúp việc cho Ban giám hiệu thực hiện quản lý hành chính học thuật.",
            "mission": "<p>Tham mưu, giúp việc cho Ban Giám hiệu trong công tác quản lý hành chính, tổng hợp thông tin và điều phối các hoạt động chung của toàn trường. Văn phòng cam kết xây dựng môi trường làm việc khoa học, văn minh và tận tụy phục vụ.</p>",
            "vision": "<p>Xây dựng văn phòng số hóa hiện đại, tối ưu hóa 100% quy trình xử lý văn bản hành chính trực tuyến, hướng tới hệ thống hành chính phục vụ chuyên nghiệp, minh bạch và thân thiện đạt chuẩn ISO.</p>",
            "history": "<p>Hình thành cùng ngày thành lập trường, luôn giữ vai trò cốt lõi trong việc duy trì vận hành hệ thống hành chính của nhà trường qua các thời kỳ, đón nhận nhiều bằng khen của Bộ Giáo dục và Đào tạo.</p>",
            "research_overview": "<p>Các nhiệm vụ trọng tâm:</p><ul><li><strong>Cải cách thủ tục hành chính:</strong> Triển khai mô hình một cửa liên thông giải quyết nhanh các thủ tục hành chính cho sinh viên.</li><li><strong>Số hóa văn phòng (E-Office):</strong> Quản lý văn bản đi/đến bằng chữ ký số, tối ưu hóa lịch công tác toàn trường trực tuyến.</li></ul>",
            "seo_title": "Văn phòng Trường - Cổng hỗ trợ hành chính thủ tục một cửa",
            "seo_description": "Cổng thông tin Văn phòng Trường. Giải quyết thủ tục hành chính, phát hành văn bản chính thức của Nhà trường.",
            "slug": "van-phong-truong"
        },
        "en": {
            "name": "Office of Academic Administration",
            "description": "The administrative body assisting the Board of Rectors in school governance and coordination.",
            "mission": "<p>To advise and assist the Board of Rectors in administrative management, coordination, and university-wide organization. We commit to a professional, dedicated, and structured service.</p>",
            "vision": "<p>To build a digitized administration system, workflow-optimizing 100% of internal documentation to achieve an ISO-certified service.</p>",
            "history": "<p>Established alongside the university's foundation, playing a key role in connecting departments and archiving official records through generations.</p>",
            "research_overview": "<p>Key focus areas include:</p><ul><li><strong>Admin Reforms:</strong> Implementing one-stop portals for simplified student administrative support.</li><li><strong>Digital Office (E-Office):</strong> E-signatures and automated database archives for campus-wide coordination.</li></ul>",
            "seo_title": "Office of Academic Administration - One-stop Student Support",
            "seo_description": "Homepage of the Office of Academic Administration. Handles academic transcripts, documentation, and student registration.",
            "slug": "office-of-academic-administration"
        }
    },
    # 7. Ban lãnh đạo Trường
    "dcf37071-9b8c-4171-90ef-b64e4754b5fb": {
        "code": "BGH",
        "unit_type": "office",
        "logo_object_key": "logos/bgh-logo.png",
        "banner_object_key": "banners/bgh-banner.png",
        "phone": "+84 (24) 3754 7897",
        "email": "bgh@university.edu.vn",
        "website": "https://bgh.university.edu.vn",
        "office": "Tầng 2, Tòa nhà Hiệu bộ",
        "head_staff_id": None,
        "vi": {
            "name": "Ban lãnh đạo Trường",
            "description": "Hội đồng Trường và Ban Giám hiệu chịu trách nhiệm điều hành, chỉ đạo chiến lược phát triển của Trường.",
            "mission": "<p>Quyết định các định hướng chiến lược, kế hoạch phát triển dài hạn của Trường. Chỉ đạo toàn diện các hoạt động đào tạo, nghiên cứu khoa học, hợp tác quốc tế và phát triển cơ sở vật chất đáp ứng yêu cầu hội nhập toàn cầu.</p>",
            "vision": "<p>Đưa trường trở thành đại học đa ngành, đa lĩnh vực hàng đầu cả nước, đạt thứ hạng cao trong các bảng xếp hạng đại học uy tín thế giới (QS, THE) và là biểu tượng của đổi mới sáng tạo giáo dục.</p>",
            "history": "<p>Tập hợp các nhà quản lý, giáo sư có trình độ chuyên môn cao và tầm nhìn chiến lược sâu rộng, kế thừa truyền thống lãnh đạo qua nhiều thế hệ để dẫn dắt nhà trường vượt qua các thách thức mới.</p>",
            "research_overview": "<p>Định hướng quản trị chiến lược:</p><ul><li><strong>Quản trị đại học thông minh:</strong> Ứng dụng hệ thống ERP quản lý tài chính, nhân sự và cơ sở vật chất trực quan hóa.</li><li><strong>Phát triển bền vững:</strong> Thúc đẩy chuyển đổi số học đường, phát triển không gian học tập xanh và kết nối cộng đồng.</li></ul>",
            "seo_title": "Ban lãnh đạo Trường - Hội đồng trường và Ban giám hiệu",
            "seo_description": "Trang thông tin Ban lãnh đạo Trường. Giới thiệu Hiệu trưởng, Hiệu phó và định hướng phát triển trường đại học thông minh.",
            "slug": "ban-lanh-dao-truong"
        },
        "en": {
            "name": "University Board of Rectors",
            "description": "Governing body steering the university towards strategic educational excellence.",
            "mission": "<p>Defining long-term visions and goals. The Board oversees academic quality, research outputs, international relations, and campus expansions to comply with global integration.</p>",
            "vision": "<p>To establish a leading multi-disciplinary research institution in engineering and technology, ranking highly in regional and global lists (QS, THE).</p>",
            "history": "<p>Composed of experienced scientists and education strategists, inheriting a legacy of excellence to lead the university through modern changes.</p>",
            "research_overview": "<p>Strategic governance directions:</p><ul><li><strong>Smart Governance:</strong> Deploying campus-wide ERP software to visualize financials and human resources.</li><li><strong>Sustainability:</strong> Accelerating paperless workflows, building green spaces, and fostering community impact.</li></ul>",
            "seo_title": "University Board of Rectors - Strategic Governance",
            "seo_description": "Board of Rectors official portal. Profiles of the Rector, Vice-Rectors, and strategic development goals.",
            "slug": "board-of-rectors"
        }
    },
    # 8. Trung tâm Kiểm thử và Đánh giá chất lượng (Rename from Khoa Kiểm Thử Hệ Thống (Cập nhật))
    "2c1ae2d4-29fa-423d-88da-16265b9df669": {
        "code": "CTE",
        "unit_type": "center",
        "logo_object_key": "logos/cte-logo.png",
        "banner_object_key": "banners/cte-banner.png",
        "phone": "+84 (24) 3754 7898",
        "email": "cte@university.edu.vn",
        "website": "https://cte.university.edu.vn",
        "office": "Tầng 3, Tòa nhà Hiệu bộ",
        "head_staff_id": "36b6a12f-560b-44c2-a660-d819004b2929", # Đặng Hồng Lĩnh
        "vi": {
            "name": "Trung tâm Kiểm thử và Đánh giá chất lượng",
            "description": "Đơn vị chuyên trách kiểm định chất lượng chương trình học, khảo thí độc lập và phát triển hệ thống ngân hàng đề thi chuyên nghiệp.",
            "mission": "<p>Tổ chức đánh giá, đo lường khách quan kết quả học tập của người học và thực hiện tự đánh giá, kiểm định chất lượng giáo dục theo tiêu chuẩn quốc gia và quốc tế. Trung tâm cam kết đồng hành cùng các khoa nâng cao liên tục chất lượng dạy và học.</p>",
            "vision": "<p>Trở thành trung tâm khảo thí độc lập uy tín cao trong nước, đạt chuẩn năng lực quốc tế về đánh giá chất lượng giáo dục đại học, cung cấp dịch vụ đánh giá chứng chỉ chuyên nghiệp cho xã hội.</p>",
            "history": "<p>Thành lập để chuyên môn hóa sâu công tác thi và kiểm định chất lượng, trung tâm đã xây dựng thành công ngân hàng câu hỏi thi trắc nghiệm khách quan chuẩn hóa cho hàng trăm học phần toàn trường.</p>",
            "research_overview": "<p>Các hướng nghiên cứu khảo thí:</p><ul><li><strong>Lý thuyết Khảo thí hiện đại (IRT):</strong> Phân tích định lượng độ phân biệt và độ khó của các câu hỏi thi để chuẩn hóa đề thi.</li><li><strong>Accreditation (Kiểm định):</strong> Phát triển hệ thống tự động theo dõi tiến độ cải tiến chất lượng sau kiểm định AUN-QA.</li></ul>",
            "seo_title": "Trung tâm Kiểm thử và Đánh giá chất lượng - Tổ chức thi & Khảo thí",
            "seo_description": "Cổng thông tin khảo thí. Tra cứu điểm thi học phần, lịch thi khảo thí, quy trình nộp đơn phúc khảo trực tuyến.",
            "slug": "trung-tam-kiem-thu-va-danh-gia-chat-luong"
        },
        "en": {
            "name": "Center for Testing and Quality Assurance",
            "description": "Specializing in academic curriculum accreditation, independent testing, and exam bank development.",
            "mission": "<p>To conduct transparent, objective student evaluations and steer institutional self-assessments. We partner with academic faculties to drive continuous teaching quality improvements.</p>",
            "vision": "<p>To grow into a nationally trusted testing center, recognized under regional QA metrics, and offering independent examination services to public partners.</p>",
            "history": "<p>Founded to professionalize exams and quality assurance. CTE has built standardized test question banks for hundreds of courses and launched secure computer-based examinations.</p>",
            "research_overview": "<p>Accreditation and test research focus on:</p><ul><li><strong>Item Response Theory (IRT):</strong> Mathematical modeling of question difficulty to refine standard exams.</li><li><strong>QA Dashboards:</strong> Automated progress tracking of action plans following AUN-QA accreditations.</li></ul>",
            "seo_title": "Center for Testing and Quality Assurance - Accreditation & Exam Portal",
            "seo_description": "Accreditation and QA center. Access student grade lookups, computer-based exam schedules, and QA reports.",
            "slug": "center-for-testing-and-quality-assurance"
        }
    },
    # 9. Khoa Khoa học máy tính và Trí tuệ nhân tạo (ID: ad04f537-60de-473a-824c-ba8f17af1f1d) - Cập nhật bỏ h3
    "ad04f537-60de-473a-824c-ba8f17af1f1d": {
        "code": "FCSAI",
        "unit_type": "faculty",
        "logo_object_key": "logos/cs-ai-logo.png",
        "banner_object_key": "banners/cs-ai-banner.png",
        "phone": "+84 (24) 3754 7890",
        "email": "cs.ai@university.edu.vn",
        "website": "https://cs-ai.university.edu.vn",
        "office": "Tầng 5, Tòa nhà C2, Khu Đô thị Đại học",
        "head_staff_id": "43395772-c785-4e9a-ba17-8fabe8599ca1", # Phan Anh Phong
        "vi": {
            "name": "Khoa Khoa học máy tính và Trí tuệ nhân tạo",
            "description": "Khoa Khoa học máy tính và Trí tuệ nhân tạo (CS&AI) là trung tâm đào tạo và nghiên cứu hàng đầu về công nghệ số.",
            "mission": "<p>Chúng tôi cam kết cung cấp môi trường giáo dục tiên tiến, thúc đẩy sự sáng tạo và nghiên cứu đỉnh cao trong lĩnh vực khoa học máy tính và trí tuệ nhân tạo. Sứ mệnh của khoa bao gồm:</p><ul><li><strong>Đào tạo xuất sắc:</strong> Cung cấp chương trình đào tạo đạt chuẩn quốc tế, giúp sinh viên phát triển tư duy phản biện, kỹ năng giải quyết vấn đề và năng lực nghiên cứu khoa học.</li><li><strong>Nghiên cứu sáng tạo:</strong> Thực hiện các nghiên cứu tiên phong, ứng dụng AI để giải quyết các thách thức lớn của xã hội, kinh tế và môi trường.</li><li><strong>Hợp tác phát triển:</strong> Xây dựng mối quan hệ đối tác chiến lược với các doanh nghiệp công nghệ hàng đầu toàn cầu và các tổ chức nghiên cứu uy tín quốc tế.</li></ul>",
            "vision": "<p>Trở thành khoa nghiên cứu và đào tạo hàng đầu trong khu vực Đông Nam Á về Khoa học máy tính và Trí tuệ nhân tạo, là nơi hội tụ các nhà khoa học xuất sắc, các sinh viên ưu tú và đối tác công nghệ chiến lược toàn cầu.</p>",
            "history": "<p>Được thành lập từ việc nâng cấp Bộ môn Khoa học máy tính và Trung tâm Nghiên cứu AI tiên tiến, khoa đã nhanh chóng khẳng định vị trí dẫn đầu của mình tại trường:</p><ul><li><strong>2015:</strong> Thành lập nhóm nghiên cứu Trí tuệ nhân tạo đầu tiên của trường.</li><li><strong>2018:</strong> Ra mắt chuyên ngành đào tạo Trí tuệ nhân tạo bậc Đại học chính quy đầu tiên.</li><li><strong>2022:</strong> Chính thức thành lập Khoa Khoa học máy tính và Trí tuệ nhân tạo để đáp ứng nhu cầu nhân lực chất lượng cao của kỷ nguyên số.</li></ul>",
            "research_overview": "<p>Khoa tập trung nguồn lực vào các lĩnh vực nghiên cứu hiện đại mang tính thực tiễn cao:</p><ol><li><strong>Trí tuệ nhân tạo (AI) & Học máy (Machine Learning):</strong> Phát triển thuật toán học sâu, mô hình ngôn ngữ lớn (LLMs), học tăng cường.</li><li><strong>Xử lý ngôn ngữ tự nhiên (NLP):</strong> Nghiên cứu công nghệ giọng nói và dịch thuật tự động cho tiếng Việt và các ngôn ngữ khu vực.</li><li><strong>Thị giác máy tính (Computer Vision):</strong> Ứng dụng nhận dạng khuôn mặt, phân tích hình ảnh y tế, xe tự hành.</li><li><strong>Khoa học dữ liệu (Data Science):</strong> Phân tích dữ liệu lớn (Big Data), khai phá tri thức ứng dụng trong tài chính và y tế.</li></ol>",
            "seo_title": "Khoa Khoa học máy tính và Trí tuệ nhân tạo (CS & AI)",
            "seo_description": "Trang chủ Khoa Khoa học máy tính và Trí tuệ nhân tạo. Thông tin chi tiết về chương trình đào tạo, hướng nghiên cứu, cơ sở vật chất và giảng viên.",
            "slug": "khoa-khoa-hoc-may-tinh-va-tri-tue-nhan-tao"
        },
        "en": {
            "name": "Faculty of Computer Science and Artificial Intelligence",
            "description": "The Faculty of Computer Science and Artificial Intelligence (CS&AI) is a leading center for education and research in digital technology.",
            "mission": "<p>We are dedicated to providing a cutting-edge education, fostering breakthrough research in computer science and artificial intelligence. Our mission encompasses:</p><ul><li><strong>Educational Excellence:</strong> Delivering international standard curriculums that foster critical thinking, problem-solving, and scientific research capabilities.</li><li><strong>Innovative Research:</strong> Conducting pioneering research and applying AI to address grand challenges in society, economy, and environment.</li><li><strong>Global Collaboration:</strong> Establishing strategic partnerships with top tech corporations and world-class research institutes.</li></ul>",
            "vision": "<p>To become a leading research and educational institution in Southeast Asia for Computer Science and Artificial Intelligence, serving as a hub for outstanding scientists, brilliant students, and global strategic technology partners.</p>",
            "history": "<p>Originating from the Department of Computer Science and the Advanced AI Research Lab, the faculty quickly grew into a leading force:</p><ul><li><strong>2015:</strong> Formed the first AI research group at the university.</li><li><strong>2018:</strong> Launched the first formal undergraduate program in Artificial Intelligence.</li><li><strong>2022:</strong> Officially established the Faculty of Computer Science and Artificial Intelligence to meet the soaring demand for digital talents.</li></ul>",
            "research_overview": "<p>Our faculty focuses on highly practical and modern research fields:</p><ol><li><strong>Artificial Intelligence & Machine Learning:</strong> Deep learning architectures, LLMs, reinforcement learning.</li><li><strong>Natural Language Processing (NLP):</strong> Speech technology and machine translation tailored for Vietnamese and regional languages.</li><li><strong>Computer Vision:</strong> Facial recognition, medical image analysis, autonomous systems.</li><li><strong>Data Science & Big Data:</strong> Analyzing large-scale datasets, knowledge discovery applied in finance and healthcare.</li></ol>",
            "seo_title": "Faculty of Computer Science and Artificial Intelligence (CS & AI)",
            "seo_description": "Official website of the Faculty of Computer Science and Artificial Intelligence. Learn more about our academic programs, research directions, faculty members, and campus facilities.",
            "slug": "faculty-of-computer-science-and-artificial-intelligence"
        }
    }
}

async def populate_all():
    print("=== POPULATING REAL EXQUISITE SEED DATA WITHOUT H3 TITLES ===")
    db = SessionLocal()
    try:
        vi_lang = (await db.execute(select(Language).where(Language.code == "vi"))).scalar_one()
        en_lang = (await db.execute(select(Language).where(Language.code == "en"))).scalar_one()
        
        # 1. Soft-delete trash department
        trash_id = uuid.UUID("ab7d5806-e8a7-49b5-81af-ccbf70ba04d9")
        trash_dept = (await db.execute(select(Department).where(Department.id == trash_id))).scalar_one_or_none()
        if trash_dept:
            trash_dept.deleted_at = datetime.now(UTC)
            print("Đã dọn dẹp (soft delete) bộ môn rác")
            
        # 2. Update each target department
        for dept_str, data in DEPARTMENTS_DATA.items():
            dept_id = uuid.UUID(dept_str)
            dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalar_one_or_none()
            if not dept:
                print(f"Cảnh báo: Không tìm thấy đơn vị {dept_str}")
                continue
                
            # Cập nhật thông tin cơ bản
            dept.code = data["code"]
            dept.unit_type = data["unit_type"]
            dept.logo_object_key = data["logo_object_key"]
            dept.banner_object_key = data["banner_object_key"]
            dept.phone = data["phone"]
            dept.email = data["email"]
            dept.website = data["website"]
            dept.office = data["office"]
            dept.head_staff_id = uuid.UUID(data["head_staff_id"]) if data["head_staff_id"] else None
            
            # Xử lý bản dịch Tiếng Việt
            vi_trans = (await db.execute(
                select(DepartmentTranslation).where(
                    DepartmentTranslation.department_id == dept_id,
                    DepartmentTranslation.language_id == vi_lang.id
                )
            )).scalar_one_or_none()
            
            if not vi_trans:
                vi_trans = DepartmentTranslation(
                    department_id=dept_id,
                    language_id=vi_lang.id,
                    **data["vi"]
                )
                db.add(vi_trans)
            else:
                for k, v in data["vi"].items():
                    setattr(vi_trans, k, v)
                db.add(vi_trans)
                
            # Xử lý bản dịch Tiếng Anh
            en_trans = (await db.execute(
                select(DepartmentTranslation).where(
                    DepartmentTranslation.department_id == dept_id,
                    DepartmentTranslation.language_id == en_lang.id
                )
            )).scalar_one_or_none()
            
            if not en_trans:
                en_trans = DepartmentTranslation(
                    department_id=dept_id,
                    language_id=en_lang.id,
                    **data["en"]
                )
                db.add(en_trans)
            else:
                for k, v in data["en"].items():
                    setattr(en_trans, k, v)
                db.add(en_trans)
                
            print(f"-> Đã cập nhật (không tiêu đề h3): {data['vi']['name']}")
            
        await db.commit()
        print("\n=== HOÀN THÀNH CẬP NHẬT FULL DATA CHUẨN KỸ THUẬT CHO FE! ===")
    except Exception as e:
        await db.rollback()
        print(f"Lỗi: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(populate_all())
