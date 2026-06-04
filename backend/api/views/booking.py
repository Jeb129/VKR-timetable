from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from api.models import Booking, BookingType
from api.serializers.requests import BookingActionSerializer, BookingCreateUpdateSerializer, BookingReadSerializer, BookingSerializer, BookingTypeSerializer
from authentification.permissions import IsBookingModerator, IsEmailVerified, IsOwner, IsOwnerAndPending

class BookingTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BookingType.objects.all().order_by('name')
    serializer_class = BookingTypeSerializer

class BookingViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return BookingReadSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return BookingCreateUpdateSerializer
        if self.action == 'reject':
            return BookingActionSerializer
        return BookingReadSerializer
    
    def get_permissions(self):
        """
        Логика прав доступа:
        - list, retrieve: Доступно всем (AllowAny)
        - create: Только пользователям с подтвержденным Email (IsEmailVerified)
        - update, partial_update: Только владельцу заявки ИЛИ модератору (IsOwner | IsBookingModerator)
        - approve, reject, destroy: Только модератору (IsBookingModerator)
        """
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [AllowAny]
        
        elif self.action == 'create':
            self.permission_classes = [IsEmailVerified]
        
        elif self.action in ['update', 'partial_update','destroy']:
            # Используем объединение прав: Владелец ИЛИ Модератор
            self.permission_classes = [IsOwnerAndPending | IsBookingModerator]
        
        elif self.action in ['approve', 'reject']:
            self.permission_classes = [IsBookingModerator]
        
        else:
            # На всякий случай для прочих методов
            self.permission_classes = [IsAuthenticated]

        return super().get_permissions()

    def perform_create(self, serializer):
        # Автоматически привязываем текущего пользователя при создании
        serializer.save(user=self.request.user)

    # Фильтр заявок закрытых
    def get_queryset(self):
        queryset = Booking.objects.all()
        # Получаем статус из ссылки (?status=0)
        status_param = self.request.query_params.get("status")
        my_param = self.request.query_params.get("my")

        if status_param is not None:
            # Если параметр передан, фильтруем по нему
            queryset = queryset.filter(status=status_param)
        if my_param == "true":
            # Фильтруем по текущему пользователю из токена
            queryset = queryset.filter(user=self.request.user)
        return queryset.order_by("-created_at")
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Метод одобрения переноса пары"""
        obj = self.get_object()
        obj.status = 1  # VERIFIED
        obj.save()
        return Response({'status': 'verified'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Метод отклонения переноса пары"""
        obj = self.get_object()
        comment = request.data.get("admin_comment")
        if not comment:
            return Response({"detail": "Причина отказа обязательна"}, status=status.HTTP_400_BAD_REQUEST)
        
        obj.status = 2  # REJECTED
        obj.admin_comment = comment
        obj.save()
        return Response({'status': 'rejected'}, status=status.HTTP_200_OK)
