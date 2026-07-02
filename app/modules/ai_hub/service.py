import uuid
from typing import List, Optional
from sqlalchemy import select, desc, asc, func, not_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai_hub.models import AIRequestLog
from app.modules.auth.models import User
from app.modules.ai_hub.schemas.admin import AISpendItem, AIUserSpendItem


class AIHubService:
    async def get_logs(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        model: Optional[str] = None,
        status_filter: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        model_type: Optional[str] = None,
    ) -> tuple[int, List[AIRequestLog]]:
        """
        Lấy danh sách logs phân trang kèm theo bộ lọc model, status, user_id và model_type.
        """
        # 1. Tính tổng số lượng
        count_query = select(func.count(AIRequestLog.id))
        
        if model:
            count_query = count_query.where(AIRequestLog.model == model)
        if status_filter:
            count_query = count_query.where(AIRequestLog.status == status_filter)
        if user_id:
            count_query = count_query.where(AIRequestLog.user_id == user_id)
            
        # Bộ lọc phân loại mô hình (Chat / Embedding)
        if model_type == "embedding":
            count_query = count_query.where(AIRequestLog.model.ilike("%embed%"))
        elif model_type == "chat":
            count_query = count_query.where(not_(AIRequestLog.model.ilike("%embed%")))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 2. Lấy dữ liệu phân trang
        data_query = select(AIRequestLog).order_by(desc(AIRequestLog.created_at))
        
        if model:
            data_query = data_query.where(AIRequestLog.model == model)
        if status_filter:
            data_query = data_query.where(AIRequestLog.status == status_filter)
        if user_id:
            data_query = data_query.where(AIRequestLog.user_id == user_id)
            
        if model_type == "embedding":
            data_query = data_query.where(AIRequestLog.model.ilike("%embed%"))
        elif model_type == "chat":
            data_query = data_query.where(not_(AIRequestLog.model.ilike("%embed%")))

        offset = (page - 1) * page_size
        data_query = data_query.offset(offset).limit(page_size)

        result = await db.execute(data_query)
        items = list(result.scalars().all())

        return total, items

    async def get_spend_statistics(
        self,
        db: AsyncSession,
        period: str = "day",
        model_type: Optional[str] = None,
    ) -> tuple[List[AISpendItem], List[AIUserSpendItem]]:
        """
        Thống kê tổng chi phí và lượng token sử dụng theo mốc thời gian (ngày, tháng, năm, toàn bộ),
        hỗ trợ lọc theo loại model (Chat / Embedding) và phân bổ theo người dùng.
        """
        # --- 1. QUERY TIME SERIES (THEO THỜI GIAN) ---
        if period == "day":
            date_format = "YYYY-MM-DD"
            limit_val = 30
        elif period == "month":
            date_format = "YYYY-MM"
            limit_val = 12
        elif period == "year":
            date_format = "YYYY"
            limit_val = 5
        else:  # all time
            date_format = "YYYY"
            limit_val = 100

        date_str = func.to_char(AIRequestLog.created_at, date_format).label("date")
        time_query = (
            select(
                date_str,
                func.sum(AIRequestLog.cost).label("total_cost"),
                func.sum(AIRequestLog.tokens_prompt + AIRequestLog.tokens_completion).label("total_tokens"),
                func.count(AIRequestLog.id).label("total_requests")
            )
            .group_by(date_str)
            .order_by(asc(date_str))
            .limit(limit_val)
        )
        
        # Áp dụng bộ lọc loại mô hình
        if model_type == "embedding":
            time_query = time_query.where(AIRequestLog.model.ilike("%embed%"))
        elif model_type == "chat":
            time_query = time_query.where(not_(AIRequestLog.model.ilike("%embed%")))

        time_result = await db.execute(time_query)
        time_rows = time_result.all()

        time_series = []
        for row in time_rows:
            time_series.append(
                AISpendItem(
                    label=row.date,
                    total_cost=float(row.total_cost or 0.0),
                    total_tokens=int(row.total_tokens or 0),
                    total_requests=int(row.total_requests or 0)
                )
            )

        # --- 2. QUERY USER SPEND (THEO NGƯỜI DÙNG) ---
        user_query = (
            select(
                AIRequestLog.user_id,
                AIRequestLog.username,
                func.coalesce(User.full_name, "Hệ thống").label("full_name"),
                func.sum(AIRequestLog.cost).label("total_cost"),
                func.sum(AIRequestLog.tokens_prompt + AIRequestLog.tokens_completion).label("total_tokens"),
                func.count(AIRequestLog.id).label("total_requests")
            )
            .outerjoin(User, AIRequestLog.user_id == User.id)
        )
        
        if model_type == "embedding":
            user_query = user_query.where(AIRequestLog.model.ilike("%embed%"))
        elif model_type == "chat":
            user_query = user_query.where(not_(AIRequestLog.model.ilike("%embed%")))
            
        user_query = (
            user_query
            .group_by(AIRequestLog.user_id, AIRequestLog.username, User.full_name)
            .order_by(desc("total_cost"))
        )

        user_result = await db.execute(user_query)
        user_rows = user_result.all()

        user_spend = []
        for row in user_rows:
            # Nếu user_id rỗng nhưng có username từ test script, giữ nguyên username
            disp_name = row.full_name
            if not row.user_id and row.username:
                disp_name = f"Script ({row.username})"
            elif not row.user_id and not row.username:
                disp_name = "Hệ thống"

            user_spend.append(
                AIUserSpendItem(
                    user_id=row.user_id,
                    username=row.username or "system",
                    full_name=disp_name,
                    total_cost=float(row.total_cost or 0.0),
                    total_tokens=int(row.total_tokens or 0),
                    total_requests=int(row.total_requests or 0)
                )
            )

        return time_series, user_spend


ai_hub_service = AIHubService()
