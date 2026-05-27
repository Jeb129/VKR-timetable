from rest_framework import permissions

class IsEmailVerified(permissions.IsAuthenticated):
    """
    1. Подтверждение email.
    Наследуется от IsAuthenticated (пользователь должен быть в системе).
    """
    message = "Необходимо подтвердить адрес электронной почты."

    def has_permission(self, request, view):
        # Сначала проверяем, авторизован ли пользователь (через родителя)
        if not super().has_permission(request, view):
            return False
        return bool(request.user.is_email_verified)


class IsMoodleUser(IsEmailVerified):
    """
    Пользователь с MOODLE аккаунтом.
    Наследуется от IsEmailVerified (почта должна быть подтверждена).
    """
    message = "Ваш аккаунт не связан с системой Moodle."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.moodle_id is not None


class IsInternalUser(permissions.IsAuthenticated):
    """
    Внутренний пользователь.
    Использует свойство is_internal.
    """
    message = "Доступ только для внутренних пользователей."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_internal


class IsScheduleModerator(permissions.IsAuthenticated):
    """
    Модератор расписания.
    Наследуется от IsAuthenticated.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return bool(request.user.is_schedule_moderator or request.user.is_staff)


class IsBookingModerator(permissions.IsAuthenticated):
    """
    Модератор мероприятий (бронирования).
    Наследуется от IsAuthenticated.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return bool(request.user.is_booking_moderator or request.user.is_staff)