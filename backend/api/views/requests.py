from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import Request, enums
from api.permissions import CanCreateRequestType
from api.serializers import RequestSerializer
from authentification.permissions import IsBookingModerator, IsOwnerAndPending, IsScheduleModerator


class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer

    def get_permissions(self):
        """
        Динамическое распределение прав в зависимости от действия
        """
        if self.action == 'create':
            return [CanCreateRequestType()]
        
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsScheduleModerator | IsBookingModerator | IsOwnerAndPending()]
        
        if self.action in ['approve', 'reject']:
            return [permissions.IsAuthenticated()]

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

        # 3. Оптимизация (select_related из предыдущего совета)
        return queryset.select_related(
            'user', 'excludedtimeslot', 'classroompreference', 'booking'
        ).prefetch_related('scheduleadjustment_set__lesson__scenario')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        instance = self.get_object()
        
        # Проверка прав модератора в зависимости от типа заявки
        is_schedule_type = instance.type != enums.RequestType.BOOKING
        if is_schedule_type and not request.user.is_schedule_moderator:
            return Response({"detail": "Вы не модератор расписания"}, status=403)
        if instance.type == enums.RequestType.BOOKING and not request.user.is_booking_moderator:
            return Response({"detail": "Вы не модератор бронирований"}, status=403)

        # ... логика одобрения ...
        instance.status = enums.RequestStatus.VERIFIED
        instance.admin_comment = request.data.get('admin_comment', '')
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        
        is_schedule_type = instance.type != enums.RequestType.BOOKING
        if is_schedule_type and not request.user.is_schedule_moderator:
            return Response({"detail": "Вы не модератор расписания"}, status=403)
        if instance.type == enums.RequestType.BOOKING and not request.user.is_booking_moderator:
            return Response({"detail": "Вы не модератор бронирований"}, status=403)
        
        admin_comment = request.data.get('admin_comment')
        if not admin_comment:
            return Response({"admin_comment": "Обязателен для отказа"}, status=400)
            
        instance.status = enums.RequestStatus.REJECTED
        instance.admin_comment = admin_comment
        instance.save()
        return Response(self.get_serializer(instance).data)