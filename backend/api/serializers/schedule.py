from rest_framework import serializers

from api.models import Lesson, ScheduleAdjustment, Booking
from api.services.schedule.mapper import MappedEvent


class MappedEventSerializer(serializers.Serializer):
    '''Сереализует в формат для отображения через FullCalendar'''
    type = serializers.CharField()
    start = serializers.DateTimeField(source="date_start")
    end = serializers.DateTimeField(source="date_end")
    title = serializers.SerializerMethodField()
    extendedProps = serializers.SerializerMethodField()

    def get_extendedProps(self, obj: MappedEvent):
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
            return {"event": LessonSerializer(obj.event).data}
        elif isinstance(obj.event, ScheduleAdjustment):
            return {"event": ScheduleAdjustmentSerializer(obj.event).data}
        elif isinstance(obj.event, Booking):
            return {"event": BookingSerializer(obj.event).data}
        return None
    
    def get_title(self, obj: MappedEvent):
        return str(obj.event)