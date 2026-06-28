import pytest
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models.base import Base, BaseModel
from app.common.repositories.base import BaseRepository
from tests.conftest import engine


# 1. Declare a mock model and Pydantic schemas for repository testing
class TestEntity(BaseModel):
    __tablename__ = "test_entity"
    name: Mapped[str] = mapped_column(String, nullable=False)


class TestEntityCreate(PydanticBaseModel):
    name: str


class TestEntityUpdate(PydanticBaseModel):
    name: str


# 2. Instantiate repository for the mock model
class TestEntityRepository(
    BaseRepository[TestEntity, TestEntityCreate, TestEntityUpdate]
):
    pass


test_repo = TestEntityRepository(TestEntity)


@pytest.fixture(autouse=True)
async def setup_local_test_tables():
    """
    Ensures that the local TestEntity table is created in the test database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_repository_crud_lifecycle(db_session: AsyncSession):
    """
    Verifies base repository CRUD operations (Create, Read, Update, Delete).
    """
    # CREATE
    obj_in = TestEntityCreate(name="Original Name")
    db_obj = await test_repo.create(db_session, obj_in=obj_in)
    await db_session.commit()

    assert db_obj.id is not None
    assert db_obj.name == "Original Name"
    assert db_obj.created_at is not None

    # READ
    fetched_obj = await test_repo.get(db_session, db_obj.id)
    assert fetched_obj is not None
    assert fetched_obj.id == db_obj.id
    assert fetched_obj.name == "Original Name"

    # UPDATE
    obj_update = TestEntityUpdate(name="Updated Name")
    updated_obj = await test_repo.update(
        db_session, db_obj=fetched_obj, obj_in=obj_update
    )
    await db_session.commit()

    assert updated_obj.name == "Updated Name"

    # GET MULTI
    all_objs = await test_repo.get_multi(db_session, skip=0, limit=10)
    assert len(all_objs) == 1
    assert all_objs[0].name == "Updated Name"

    # DELETE
    deleted_obj = await test_repo.delete(db_session, id=db_obj.id)
    await db_session.commit()
    assert deleted_obj is not None
    assert deleted_obj.id == db_obj.id

    # Verify lookup returns None after delete
    fetched_after_delete = await test_repo.get(db_session, db_obj.id)
    assert fetched_after_delete is None
