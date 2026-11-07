from datetime import datetime, timedelta, timezone

from app.notifications.model.notification_orm import NotificationORM
from app.notifications.service import notification_service


def _notification_payload(scheduled_at: datetime | None = None) -> dict:
    return {
        "content": "Integration-test notification",
        "channel": "EMAIL",
        "recipient": "student@example.com",
        "scheduled_at": (scheduled_at or datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "timezone": "UTC",
    }


def test_notifications_crud_and_status_flow(client):
    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0)
    payload = {
        "content": "Reminder for lecture",
        "channel": "EMAIL",
        "recipient": "student@example.com",
        "scheduled_at": scheduled_at.isoformat(),
        "timezone": "Europe/Warsaw",
    }

    create_response = client.post("/api/v1/notifications", json=payload)
    assert create_response.status_code == 201, create_response.text
    body = create_response.json()
    assert body["content"] == payload["content"]
    assert body["channel"] == "EMAIL"
    assert body["status"] == "PENDING"

    notification_id = body["id"]

    list_response = client.get("/api/v1/notifications")
    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == notification_id for item in list_response.json())

    fetch_response = client.get(f"/api/v1/notifications/{notification_id}")
    assert fetch_response.status_code == 200, fetch_response.text
    assert fetch_response.json()["recipient"] == payload["recipient"]

    patch_response = client.patch(
        f"/api/v1/notifications/{notification_id}/status",
        json={"status": "SENT"},
    )
    assert patch_response.status_code == 200, patch_response.text
    assert patch_response.json()["status"] == "SENT"

    bad_update = client.patch(
        f"/api/v1/notifications/{notification_id}/status",
        json={"status": "PENDING"},
    )
    assert bad_update.status_code == 422, bad_update.text


def test_send_now_sends_future_notification(client, monkeypatch):
    sent_ids = []
    monkeypatch.setattr(
        notification_service,
        "dispatch_notification",
        lambda notification: sent_ids.append(notification.id),
    )

    create_response = client.post(
        "/api/v1/notifications",
        json=_notification_payload(),
    )
    assert create_response.status_code == 201, create_response.text
    notification_id = create_response.json()["id"]

    response = client.post(f"/api/v1/notifications/{notification_id}/send-now")

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "SENT"
    assert sent_ids == [notification_id]


def test_create_notification_rejects_past_schedule(client):
    response = client.post(
        "/api/v1/notifications",
        json=_notification_payload(datetime.now(timezone.utc) - timedelta(minutes=1)),
    )

    assert response.status_code == 422, response.text


def test_process_ready_sends_due_notifications(client, db_session, monkeypatch):
    sent_ids = []
    monkeypatch.setattr(
        notification_service,
        "dispatch_notification",
        lambda notification: sent_ids.append(notification.id),
    )

    create_response = client.post(
        "/api/v1/notifications",
        json=_notification_payload(),
    )
    assert create_response.status_code == 201, create_response.text
    notification_id = create_response.json()["id"]

    notification = db_session.get(NotificationORM, notification_id)
    assert notification is not None
    notification.scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.flush()

    response = client.post("/api/v1/notifications/process-ready")

    assert response.status_code == 200, response.text
    assert response.json() == {"processed_count": 1}
    assert sent_ids == [notification_id]

    get_response = client.get(f"/api/v1/notifications/{notification_id}")
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["status"] == "SENT"
