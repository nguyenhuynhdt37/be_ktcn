import asyncio
import sys
import os
from loguru import logger
from sqlalchemy import select, update

# Thêm project root vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.faculty_staff.models import Department, Position, Staff

async def activate_all():
    async with SessionLocal() as db:
        logger.info("⚡ Đang kích hoạt lại trạng thái hoạt động cho toàn bộ Departments, Positions, Staffs...")
        
        # 1. Kích hoạt Departments
        dept_stmt = update(Department).where(Department.deleted_at.is_(None)).values(is_active=True)
        res_dept = await db.execute(dept_stmt)
        
        # 2. Kích hoạt Positions
        pos_stmt = update(Position).where(Position.deleted_at.is_(None)).values(is_active=True)
        res_pos = await db.execute(pos_stmt)
        
        # 3. Kích hoạt Staffs
        staff_stmt = update(Staff).where(Staff.deleted_at.is_(None)).values(is_active=True)
        res_staff = await db.execute(staff_stmt)
        
        await db.commit()
        
        logger.info(f"✅ Kích hoạt thành công:")
        logger.info(f"   - {res_dept.rowcount} bộ môn")
        logger.info(f"   - {res_pos.rowcount} chức vụ")
        logger.info(f"   - {res_staff.rowcount} giảng viên")

if __name__ == "__main__":
    asyncio.run(activate_all())
