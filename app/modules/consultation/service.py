import uuid
import csv
import io
import random
from datetime import datetime, UTC, timedelta
from typing import Optional, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.consultation.models import Consultation, ConsultationStatus
from app.modules.consultation.schemas import ConsultationCreate, ConsultationUpdate
from app.modules.consultation.sse import sse_manager


class ConsultationService:
    """
    Nghiệp vụ quản lý các yêu cầu tư vấn tuyển sinh (Leads).
    """

    async def create_consultation(
        self, db: AsyncSession, payload: ConsultationCreate
    ) -> Consultation:
        """
        Tạo yêu cầu tư vấn mới từ Portal.
        Có validation, chống bot (honeypot), chống trùng số trong 24h và tự động sinh mã yêu cầu.
        """
        # 1. Chống bot bằng Honeypot
        if payload.website and len(payload.website.strip()) > 0:
            # Nếu honeypot field có giá trị, coi là spam bot và từ chối xử lý
            raise BadRequestException(
                message="Yêu cầu bị từ chối do phát hiện bot.",
                error_code="BOT_DETECTED"
            )

        # 2. Chuẩn hóa số điện thoại
        phone_stripped = payload.phone.strip()

        # 3. Chống trùng số điện thoại trong vòng 24 giờ
        time_limit = datetime.now(UTC) - timedelta(hours=24)
        duplicate_query = select(Consultation).where(
            Consultation.phone == phone_stripped,
            Consultation.created_at >= time_limit
        )
        duplicate_result = await db.execute(duplicate_query)
        if duplicate_result.scalars().first():
            raise BadRequestException(
                message="Số điện thoại này đã gửi yêu cầu tư vấn trong vòng 24 giờ qua.",
                error_code="DUPLICATE_CONSULTATION"
            )

        # 4. Tự động tạo mã yêu cầu duy nhất: TV-YYYYMMDD-XXXX (4 chữ số ngẫu nhiên)
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        
        # Thử sinh mã ngẫu nhiên không trùng tối đa 10 lần
        request_code = ""
        for _ in range(10):
            rand_val = random.randint(1000, 9999)
            code_candidate = f"TV-{date_str}-{rand_val}"
            
            code_query = select(Consultation).where(Consultation.request_code == code_candidate)
            code_result = await db.execute(code_query)
            if not code_result.scalars().first():
                request_code = code_candidate
                break
                
        if not request_code:
            # Fallback nếu xui xẻo trùng hết 10 lần
            request_code = f"TV-{date_str}-{random.randint(100000, 999999)}"

        # 5. Lưu vào database
        consultation = Consultation(
            id=uuid.uuid4(),
            request_code=request_code,
            fullname=payload.full_name.strip(),
            phone=phone_stripped,
            email=payload.email.strip() if payload.email else None,
            status=ConsultationStatus.PENDING,
            notes=payload.message.strip() if payload.message else None
        )
        db.add(consultation)
        await db.flush()

        # 6. Phát thông báo realtime SSE cho admin
        # Sử dụng lazy import hoặc chuẩn bị data minified để gửi qua SSE
        sse_data = {
            "id": str(consultation.id),
            "request_code": consultation.request_code,
            "fullname": consultation.fullname,
            "phone": consultation.phone,
            "email": consultation.email,
            "notes": consultation.notes,
            "status": consultation.status.value,
            "created_at": consultation.created_at.isoformat()
        }
        # Phát SSE không chặn luồng chính
        import asyncio
        asyncio.create_task(sse_manager.pub_event("new_consultation", sse_data))

        return consultation

    async def list_consultations(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[ConsultationStatus] = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> tuple[list[Consultation], int]:
        """
        Lấy danh sách các yêu cầu tư vấn hỗ trợ tìm kiếm, lọc và phân trang (dành cho Admin).
        """
        skip = (page - 1) * page_size

        # Query chính
        query = select(Consultation).options(selectinload(Consultation.assignee))
        count_query = select(func.count(Consultation.id))

        # Lọc theo trạng thái
        if status:
            query = query.where(Consultation.status == status)
            count_query = count_query.where(Consultation.status == status)

        # Tìm kiếm theo họ tên, sđt, email, mã yêu cầu
        if search:
            search_term = f"%{search.strip()}%"
            search_filter = (
                Consultation.fullname.ilike(search_term)
                | Consultation.phone.ilike(search_term)
                | Consultation.email.ilike(search_term)
                | Consultation.request_code.ilike(search_term)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Đếm tổng
        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0

        # Sắp xếp
        sort_attr = getattr(Consultation, sort_by, Consultation.created_at)
        if order.lower() == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())

        # Phân trang
        query = query.offset(skip).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_consultation_by_id(self, db: AsyncSession, consultation_id: uuid.UUID) -> Consultation:
        """Lấy chi tiết yêu cầu tư vấn."""
        query = select(Consultation).where(Consultation.id == consultation_id).options(selectinload(Consultation.assignee))
        result = await db.execute(query)
        db_obj = result.scalars().first()
        if not db_obj:
            raise NotFoundException(
                message="Không tìm thấy yêu cầu tư vấn",
                error_code="CONSULTATION_NOT_FOUND"
            )
        return db_obj

    async def update_consultation(
        self, db: AsyncSession, consultation_id: uuid.UUID, payload: ConsultationUpdate, current_admin_id: uuid.UUID
    ) -> Consultation:
        """
        Cập nhật trạng thái, nhận xử lý, ghi chú yêu cầu tư vấn.
        """
        db_obj = await self.get_consultation_by_id(db, consultation_id)

        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def export_csv(
        self, db: AsyncSession, search: Optional[str] = None, status: Optional[ConsultationStatus] = None
    ) -> str:
        """
        Xuất toàn bộ danh sách yêu cầu tư vấn ra file CSV hỗ trợ Excel (UTF-8 with BOM).
        """
        query = select(Consultation).options(selectinload(Consultation.assignee)).order_by(Consultation.created_at.desc())
        
        if status:
            query = query.where(Consultation.status == status)
            
        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                Consultation.fullname.ilike(search_term)
                | Consultation.phone.ilike(search_term)
                | Consultation.email.ilike(search_term)
                | Consultation.request_code.ilike(search_term)
            )
            
        result = await db.execute(query)
        items = result.scalars().all()

        output = io.StringIO()
        # Thêm BOM để Excel đọc đúng tiếng Việt UTF-8
        output.write('\ufeff')
        
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Tiêu đề cột
        writer.writerow([
            "Mã yêu cầu", "Họ tên", "Số điện thoại", "Email", 
            "Trạng thái", "Người xử lý", "Ghi chú", "Ngày tạo"
        ])
        
        status_map = {
            ConsultationStatus.PENDING: "Chờ xử lý",
            ConsultationStatus.PROCESSING: "Đang xử lý",
            ConsultationStatus.COMPLETED: "Đã hoàn thành",
            ConsultationStatus.CANCELLED: "Đã hủy"
        }
        
        for item in items:
            assignee_name = item.assignee.full_name if item.assignee else "Chưa gán"
            status_text = status_map.get(item.status, item.status.value)
            writer.writerow([
                item.request_code,
                item.fullname,
                item.phone,
                item.email or "",
                status_text,
                assignee_name,
                item.notes or "",
                item.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
            
        return output.getvalue()


consultation_service = ConsultationService()
