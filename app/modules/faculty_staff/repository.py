from app.common.repositories.base import BaseRepository
from app.modules.faculty_staff.models import Position, Department, Staff
from app.modules.faculty_staff.schemas import (
    PositionCreate,
    PositionUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    StaffCreate,
    StaffUpdate,
)


class PositionRepository(BaseRepository[Position, PositionCreate, PositionUpdate]):
    """
    Repository quản lý các truy vấn CRUD trên bảng positions.
    Thừa kế toàn bộ khả năng CRUD async từ BaseRepository.
    """
    def __init__(self):
        super().__init__(Position)


class DepartmentRepository(BaseRepository[Department, DepartmentCreate, DepartmentUpdate]):
    """
    Repository quản lý các truy vấn CRUD trên bảng departments.
    Thừa kế toàn bộ khả năng CRUD async từ BaseRepository.
    """
    def __init__(self):
        super().__init__(Department)


class StaffRepository(BaseRepository[Staff, StaffCreate, StaffUpdate]):
    """
    Repository quản lý các truy vấn CRUD trên bảng staffs.
    Thừa kế toàn bộ khả năng CRUD async từ BaseRepository.
    """
    def __init__(self):
        super().__init__(Staff)


position_repository = PositionRepository()
department_repository = DepartmentRepository()
staff_repository = StaffRepository()


