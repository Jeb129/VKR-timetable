from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.models import Booking
from api.serializers.requests import BookingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_class = [IsAuthenticated]

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
