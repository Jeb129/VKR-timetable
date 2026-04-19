from rest_framework import serializers
from django.db import models
from django.forms.models import model_to_dict

from api.models import Lesson, ScheduleAdjustment, Booking, ScheduleScenario
from api.serializers.education import LessonSerializer
from api.services.constraunt.meta import ConstraintError
from api.services.schedule.mapper import MappedEvent

class ScheduleScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleScenario
        fields = '__all__'

class MappedEventSerializer(serializers.Serializer):
    """Сереализует в формат для отображения через FullCalendar"""

    type = serializers.ReadOnlyField()
    start = serializers.ReadOnlyField(source="date_start")
    end = serializers.ReadOnlyField(source="date_end")
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

class ConstraintErrorSerializer(serializers.Serializer):
    name = serializers.CharField()
    penalty = serializers.IntegerField()
    message = serializers.CharField()
    data = serializers.SerializerMethodField()

    def get_data(self, obj):
        return self._serialize(obj.data)

    def _serialize(self, value):
        # Модель → сериализуем
        if isinstance(value, models.Model):
            return self._serialize_model(value)

        # Словарь → обойти рекурсивно
        if isinstance(value, dict):
            return {k: self._serialize(v) for k, v in value.items()}

        # Список/кортеж → обойти элементы
        if isinstance(value, (list, tuple)):
            return [self._serialize(v) for v in value]

        # Примитивы
        return str(value)

    def _serialize_model(self, instance):
        # Сереализуем через model_to_dict т.к. в ошибке вряд ли нужен полноценный объект.
        # Потом можно будет заменить на полноценное применение сериальзатором
        fields = [f.name for f in instance._meta.concrete_fields]
        if isinstance(instance, Lesson):
            return LessonSerializer(instance).data
        return model_to_dict(instance, fields=fields)