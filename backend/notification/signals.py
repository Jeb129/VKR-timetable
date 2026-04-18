from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models.requests import Booking
from .services import EmailNotificationService

@receiver(post_save, sender=Booking)
def booking_notification_handler(sender, instance, created, **kwargs):
    if created:
        # Если заявка только что создана
        EmailNotificationService.notify_booking_created(instance)
    else:
        # Если это обновление (модерация)
        # Проверяем, что статус изменился с "На модерации" на что-то другое
        EmailNotificationService.notify_status_update(instance)