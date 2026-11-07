from app.notifications.model.notification_orm import NotificationORM
from app.notifications.model.notification_channel import NotificationChannel
from email.message import EmailMessage
import smtplib
import requests

HANDLERS = {}

def register(name):
    def decorator(func):
        HANDLERS[name] = func
        return func
    return decorator

@register(NotificationChannel.EMAIL)
def send_email_notification(notification: NotificationORM) -> None:
    msg = EmailMessage()
    msg.set_content(notification.content)
    msg["Subject"] = "Notification"
    msg["From"] = "noreply@ztp.local"
    msg["To"] = notification.recipient

    with smtplib.SMTP("localhost", 1025) as server:
        server.send_message(msg)

@register(NotificationChannel.PUSH)
def send_push_notification(notification: NotificationORM) -> None:
    response = requests.post(
        f"http://localhost:8088/{notification.recipient}",
        data=notification.content.encode("utf-8"),
        timeout=5,
    )
    response.raise_for_status()