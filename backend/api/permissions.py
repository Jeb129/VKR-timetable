from rest_framework import permissions
from api.models import enums
from authentification.permissions import IsOwnerAndPending

class CanCreateRequestType(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        req_type = request.data.get('type')
        try:
            req_type = int(req_type)
        except (TypeError, ValueError):
            return True # Ошибку выдаст сериализатор

        is_schedule_type = req_type in [
            enums.RequestType.EXCLUDED_TIMESLOT,
            enums.RequestType.CLASSROOM_PREFERENCE,
            enums.RequestType.SCHEDULE_ADJUSTMENT
        ]

        if is_schedule_type:
            return request.user.is_schedule_moderator or (request.user.teacher is not None) 
        
        return True

class IsRequestModerator(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):
            return False
        user = request.user
        if user is None:
            return False
        
        if obj.type == enums.RequestType.BOOKING:
            return user.is_booking_moderator
        return user.is_schedule_moderator

class IsModeratorOrOwner(permissions.IsAuthenticated):
    # Костыль. Почему то логика применения прав через операнды | и & выдает ошибку, если применять в get_permission
    # Поэтому вот так
    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):
            return False
        # Проверяем первое условие
        is_moderator = IsRequestModerator().has_object_permission(request, view, obj)
        # Проверяем второе условие
        is_owner = IsOwnerAndPending().has_object_permission(request, view, obj)
        
        return is_moderator or is_owner