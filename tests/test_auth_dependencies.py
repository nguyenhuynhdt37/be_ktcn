import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_superadmin_is_exposed_as_admin_when_database_flag_is_false():
    user = SimpleNamespace(
        id=uuid.uuid4(),
        username="superadmin",
        email="superadmin@example.com",
        full_name="Super Admin",
        avatar=None,
        avatar_url=None,
        is_active=True,
        is_admin=False,
    )
    result = SimpleNamespace(scalar_one_or_none=lambda: user)
    db = AsyncMock()
    db.execute.return_value = result

    with patch(
        "app.modules.auth.dependencies.decode_access_token",
        return_value={"sub": str(user.id)},
    ):
        current_user = await get_current_user(
            access_token="valid-token",
            http_auth=None,
            db=db,
        )

    assert current_user.roles == ["super_admin"]
    assert current_user.is_admin is True
