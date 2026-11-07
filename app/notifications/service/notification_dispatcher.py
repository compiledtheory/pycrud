from app.notifications.model.notification_orm import NotificationORM
from app.notifications.model.notification_channel import NotificationChannel
from app.notifications.service.notification_delivery_service import HANDLERS as DeliveryHandlers


def dispatch_notification(notification: NotificationORM) -> None:
    if handler := DeliveryHandlers.get(NotificationChannel(notification.channel)):
        handler(notification)
        return
    raise ValueError(f"Nieobsługiwany kanał powiadomienia: {notification.channel}")
