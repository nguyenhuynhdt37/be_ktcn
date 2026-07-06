import uuid

import pytest
from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification


@pytest.mark.asyncio
async def test_create_consultation_and_prevent_duplicate(client, admin_credentials):
    del admin_credentials
    suffix = str(uuid.uuid4().int)[-8:]
    phone = f"09{suffix}"
    payload = {
        "full_name": "Thí sinh kiểm thử",
        "phone": phone,
        "email": f"candidate-{suffix}@example.com",
        "interested_major": "Công nghệ thông tin",
        "request_type": "ADMISSION_CONSULTING",
        "message": "Cần tư vấn phương thức xét tuyển",
        "consent_given": True,
        "website": "",
    }

    created_id = None
    try:
        response = await client.post("/api/v1/portal/consultations", json=payload)
        assert response.status_code == 201
        body = response.json()
        created_id = uuid.UUID(body["id"])
        assert body["reference_code"].startswith("TV")
        assert body["status"] == "NEW"
        assert body["message"] == "Yêu cầu tư vấn đã được tiếp nhận"

        duplicate = await client.post("/api/v1/portal/consultations", json=payload)
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "DUPLICATE_CONSULTATION"

        async with SessionLocal() as db:
            active_admin_count = (
                await db.execute(
                    select(func.count(User.id)).where(
                        User.is_active.is_(True),
                        User.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
            notification_count = (
                await db.execute(
                    select(func.count(Notification.id)).where(
                        Notification.related_entity_id == created_id
                    )
                )
            ).scalar_one()
            assert notification_count == active_admin_count
    finally:
        if created_id:
            async with SessionLocal() as db:
                await db.execute(
                    delete(Notification).where(
                        Notification.related_entity_id == created_id
                    )
                )
                await db.execute(
                    delete(ConsultationLead).where(ConsultationLead.id == created_id)
                )
                await db.commit()


@pytest.mark.asyncio
async def test_consultation_requires_data_consent(client):
    response = await client.post(
        "/api/v1/portal/consultations",
        json={
            "full_name": "Nguyễn Văn A",
            "phone": "0912345678",
            "email": "candidate@example.com",
            "interested_major": "Kỹ thuật phần mềm",
            "request_type": "ADMISSION_CONSULTING",
            "consent_given": False,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
