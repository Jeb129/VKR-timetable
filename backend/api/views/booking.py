from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
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
