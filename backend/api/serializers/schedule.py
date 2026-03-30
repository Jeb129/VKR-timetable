from rest_framework import serializers

from api.models import Lesson, ScheduleAdjustment, Booking
from api.services.schedule.mapper import MappedEvent


class MappedEventSerializer(serializers.Serializer):
    type = serializers.CharField()
    date_start = serializers.DateTimeField()
    date_end = serializers.DateTimeField()
    event = serializers.SerializerMethodField()

    def get_event(self, obj: MappedEvent):
        """
        Возвращает сериализованное представление поля event
        в зависимости от его типа.
        """
        from api.serializers import (
            LessonSerializer,
            ScheduleAdjustmentSerializer,
            BookingSerializer,
        )

        if isinstance(obj.event, Lesson):
            return LessonSerializer(obj.event).data
        elif isinstance(obj.event, ScheduleAdjustment):
            return ScheduleAdjustmentSerializer(obj.event).data
        elif isinstance(obj.event, Booking):
            return BookingSerializer(obj.event).data
        return None
