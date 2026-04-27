from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from api.models.enums import RequestStatus

User = get_user_model()

class EmailNotificationService:
    @staticmethod
    def _send(subject, message, recipient_list):
        """Базовый метод отправки"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=True,
        )

    @classmethod
    def notify_booking_created(cls, booking):
        """Уведомление о создании новой заявки"""
        # Письмо пользователю
        cls._send(
            subject="Ваша заявка на бронирование принята",
            message=(
                f"Здравствуйте, {booking.user.username}!\n\n"
                f"Ваша заявка на бронирование аудитории {booking.classroom.num} успешно создана "
                f"и ожидает модерации.\n"
                f"Время: {booking.date_start.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Мы сообщим вам, когда статус изменится."
            ),
            recipient_list=[booking.user.email]
        )

        # Письмо модераторам пока на is_staff
        moderators_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        if moderators_emails:
            cls._send(
                subject="Новая заявка на бронирование",
                message=(
                    f"В системе появилась новая заявка от {booking.user.email}.\n\n"
                    f"Аудитория: {booking.classroom.num}\n"
                    f"Время: {booking.date_start.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Причина: {booking.description}\n\n"
                    f"Пожалуйста, обработайте её в панели модерации."
                ),
                recipient_list=list(moderators_emails)
            )

    @classmethod
    def notify_status_update(cls, booking):
        """Уведомление об изменении статуса (Одобрено/Отклонено)"""
        user_email = booking.user.email
        
        if booking.status == RequestStatus.VERIFIED:
            subject = "Бронирование ПОДТВЕРЖДЕНО"
            message = f"Ваша заявка на аудиторию {booking.classroom.num} одобрена."
        elif booking.status == RequestStatus.REJECTED:
            subject = "Бронирование ОТКЛОНЕНО"
            message = (
                f"Ваша заявка на аудиторию {booking.classroom.num} была отклонена.\n"
                f"Причина: {booking.admin_comment or 'Не указана'}."
            )
        else:
            return

        cls._send(subject, message, [user_email])