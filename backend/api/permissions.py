from rest_framework import permissions
from api.models import enums

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