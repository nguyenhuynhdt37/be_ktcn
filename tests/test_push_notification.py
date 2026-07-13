import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notification.models import PushSubscription
from app.modules.notification.service import notification_service


@pytest.mark.asyncio
async def test_push_notification_workflow(client, db_session: AsyncSession):
    from app.core.config import settings
    settings.VAPID_PUBLIC_KEY = "BN5Yt6MEIUewAVbP-ZGflEGumFcS1jV2yjny"
    settings.VAPID_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgAa7eQUZtiRWVy5NR\nJOvPHCfmO/buex7XENNQbcUecXuhRANCAATeWLejBCFHsAFWz/mRn5RBrphXEtY1\ndso58v06vDbDkgmP0xCHhu0IJC1IDH0VPDfgJF6+qxnHZ3ManLI5AxFn\n-----END PRIVATE KEY-----"
    
    endpoint = f"https://fcm.googleapis.com/fcm/send/test-device-{uuid.uuid4()}"
    subscribe_payload = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": "BN5Yt6MEIUewAVbP-ZGflEGumFcS1jV2yjny",
            "auth": "auth_key_123"
        },
        "user_agent": "Mozilla/5.0 (Test Browser)"
    }

    # 1. Test get VAPID public key
    vapid_res = await client.get("/api/v1/portal/notifications/vapid-public-key")
    assert vapid_res.status_code == 200
    assert "public_key" in vapid_res.json()

    # 2. Test subscribe push device
    subscribe_res = await client.post("/api/v1/portal/notifications/subscribe", json=subscribe_payload)
    assert subscribe_res.status_code == 200
    assert subscribe_res.json()["success"] is True

    # 3. Test gửi push notification
    # Mock SessionLocal để trả về chính db_session của test (tránh cô lập transaction của pytest)
    mock_session_context = AsyncMock()
    mock_session_context.__aenter__.return_value = db_session
    
    with patch("app.core.database.SessionLocal", return_value=mock_session_context):
        with patch("pywebpush.webpush") as mock_webpush:
            mock_webpush.return_value = MagicMock()
            
            await notification_service.send_web_push_to_all(
                title="Thông báo mới",
                body="Nội dung thông báo thử nghiệm",
                url="/vi/thong-bao/test-slug"
            )
            
            assert mock_webpush.called
            call_args = mock_webpush.call_args[1]
            assert call_args["subscription_info"]["endpoint"] == endpoint

    # 4. Test unsubscribe
    unsubscribe_payload = {
        "endpoint": endpoint
    }
    unsubscribe_res = await client.post("/api/v1/portal/notifications/unsubscribe", json=unsubscribe_payload)
    assert unsubscribe_res.status_code == 200
    assert unsubscribe_res.json()["success"] is True

    # Kiểm tra đã bị xóa trong database chưa
    stmt = select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    res = await db_session.execute(stmt)
    sub = res.scalar_one_or_none()
    assert sub is None
