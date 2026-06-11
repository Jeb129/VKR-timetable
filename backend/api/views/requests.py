from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Request, enums
from api.pagination import StandartPagination
from api.permissions import CanCreateRequestType, IsModeratorOrOwner, IsRequestModerator
from api.serializers import RequestSerializer
from api.services.schedule.mapper import ScheduleMapper

class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    pagination_class = StandartPagination

    def get_permissions(self):
        """
        Динамическое распределение прав в зависимости от действия
        """
        if self.action == 'create':
            return [CanCreateRequestType()]
        
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsModeratorOrOwner()]
        
        if self.action in ['approve', 'reject']:
            return [IsRequestModerator()]

        # list, retrieve
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        # 1. Фильтр активного сценария для корректировок
        # Показываем корректировки только из активных сценариев, 
        # либо любые другие типы заявок
        queryset = Request.objects.filter(
            Q(type=enums.RequestType.SCHEDULE_ADJUSTMENT, 
              scheduleadjustment__lesson__scenario__is_active=True) |
            ~Q(type=enums.RequestType.SCHEDULE_ADJUSTMENT)
        ).distinct()

        # 2. Ограничение видимости по ролям
        if not user.is_superuser:
            # Условия видимости:
            # - Я автор
            # - Я модератор расписания (вижу типы расписания)
            # - Я модератор бронирования (вижу брони)
            show_conditions = Q(user=user)

            if user.is_schedule_moderator:
                show_conditions |= Q(type__in=[
                    enums.RequestType.EXCLUDED_TIMESLOT,
                    enums.RequestType.CLASSROOM_PREFERENCE,
                    enums.RequestType.SCHEDULE_ADJUSTMENT
                ])
            
            if user.is_booking_moderator:
                show_conditions |= Q(type=enums.RequestType.BOOKING)

            queryset = queryset.filter(show_conditions)

        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Фильтр по типу заявки (?type=3)
        req_type = self.request.query_params.get('type')
        if req_type:
            queryset = queryset.filter(type=req_type)
        # 3. Оптимизация (select_related из предыдущего совета)
        return queryset.select_related(
            'user', 'excludedtimeslot', 'classroompreference', 'booking'
        ).prefetch_related('scheduleadjustment_set__lesson__scenario')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        instance = self.get_object()

        if instance.type == enums.RequestType.BOOKING:
            events = ScheduleMapper(instance.booking.date_start,instance.booking.date_end,classroom_id=instance.booking.classroom_id)
            if events:
                return Response(
                    {"message":"Аудитория уже занята в это время"},
                    status = status.HTTP_409_CONFLICT
                )
            
        instance.status = enums.RequestStatus.VERIFIED
        instance.admin_comment = request.data.get('admin_comment', '')
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        instance = self.get_object()

        admin_comment = request.data.get('admin_comment')
        if not admin_comment:
            return Response({"admin_comment": "Обязателен для отказа"}, status=status.HTTP_400_BAD_REQUEST)
            
        instance.status = enums.RequestStatus.REJECTED
        instance.admin_comment = admin_comment
        instance.save()
        return Response(self.get_serializer(instance).data)
