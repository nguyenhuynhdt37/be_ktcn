"""Add SEO permissions

Revision ID: 3fa92530ace4
Revises: 580570b2d492
Create Date: 2026-06-28 23:51:06.275749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision: str = '3fa92530ace4'
down_revision: Union[str, None] = '580570b2d492'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PERMISSIONS = [
    {"id": str(uuid.uuid4()), "code": "article.seo.read", "name": "Đọc SEO bài viết", "module": "ARTICLE", "action": "READ", "description": "Xem chi tiết SEO của bài viết"},
    {"id": str(uuid.uuid4()), "code": "article.seo.update", "name": "Cập nhật SEO bài viết", "module": "ARTICLE", "action": "UPDATE", "description": "Sửa thông tin SEO của bài viết"},
    {"id": str(uuid.uuid4()), "code": "article.seo.generate", "name": "Tạo SEO bằng AI", "module": "ARTICLE", "action": "GENERATE", "description": "Sử dụng AI để tự động tạo gợi ý SEO"},
    {"id": str(uuid.uuid4()), "code": "article.seo.preview", "name": "Xem trước hiển thị SEO", "module": "ARTICLE", "action": "PREVIEW", "description": "Xem trước hiển thị bài viết trên Google, FB"},
]

def upgrade() -> None:
    # Get the permissions table
    permissions_table = sa.table(
        'permissions',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('code', sa.String()),
        sa.column('name', sa.String()),
        sa.column('module', sa.String()),
        sa.column('action', sa.String()),
        sa.column('description', sa.String()),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('updated_at', sa.DateTime(timezone=True))
    )
    
    # Insert permissions
    op.bulk_insert(
        permissions_table,
        [
            {
                "id": p["id"],
                "code": p["code"],
                "name": p["name"],
                "module": p["module"],
                "action": p["action"],
                "description": p["description"],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            for p in PERMISSIONS
        ]
    )

def downgrade() -> None:
    codes = [p["code"] for p in PERMISSIONS]
    op.execute(
        sa.text("DELETE FROM permissions WHERE code IN :codes").bindparams(codes=tuple(codes))
    )
