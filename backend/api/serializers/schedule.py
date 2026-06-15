from rest_framework import serializers
from django.db import models
from django.forms.models import model_to_dict

from api.models import Lesson, ScheduleAdjustment, Booking
from api.serializers.database import TimeslotSerializer
from api.serializers.requests import BookingReadSerializer, ScheduleAdjustmentReadSerializer
from api.services.constraints.meta import ConstraintError
from api.services.schedule.mapper import MappedEvent
from config.utils import SimpleRelatedSerializer


def fast_simple_serialize(obj, many=False):
    if many:
        return [fast_simple_serialize(item, many=False) for item in obj]
    if obj is None:
        return None
    return {
        "id": obj.pk,
        "name": getattr(obj, "name", str(obj))
    }

class LessonReadSerializer(serializers.ModelSerializer):

    # Текстовые названия из связанных моделей
    discipline = serializers.ReadOnlyField(source="discipline.name")
    lesson_type = serializers.ReadOnlyField(source="lesson_type.name")
    timeslot = TimeslotSerializer()
    classroom = serializers.ReadOnlyField(source="classroom.name")

    # Списки
    teachers = SimpleRelatedSerializer(many=True)
    study_groups = SimpleRelatedSerializer(many=True)
    
    # Поля черновика
    draft_info = serializers.SerializerMethodField()

    def get_teachers(self,obj):
        return fast_simple_serialize(obj,many=True)
    
    def get_study_groups(self,obj):
        return fast_simple_serialize(obj,many=True)

    def get_draft_info(self, obj):
        originals = getattr(obj, 'draft_originals', {})
        if not originals and not getattr(obj, 'draft_created', False):
            return None

        diffs = []
        for field, old_obj in originals.items():
            # "Текущее" (новое) значение мы берем прямо из объекта obj
            current_val = getattr(obj, field)
            is_list = isinstance(old_obj,list)
            diffs.append({
                "field": field,
                "was": fast_simple_serialize(old_obj,many=is_list),
                "now": fast_simple_serialize(current_val,many=is_list)
            })
        return {
            "is_new": getattr(obj, 'draft_created', False),
            "changes": diffs
        }
    
    class Meta:
        model = Lesson
        fields = [
            "id",
            "scenario", 
            "discipline",
            "lesson_type",
            "classroom",
            "timeslot",
            "teachers",
            "study_groups",
            "whole_weeks",
            "draft_info"
        ]

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
        if isinstance(obj.event, Lesson):
            return {"event": LessonReadSerializer(obj.event).data}
        elif isinstance(obj.event, ScheduleAdjustment):
            return {"event": ScheduleAdjustmentReadSerializer(obj.event).data}
        elif isinstance(obj.event, Booking):
            return {"event": BookingReadSerializer(obj.event).data}
        return None

    def get_title(self, obj: MappedEvent):
        return str(obj.event)

class ConstraintErrorSerializer(serializers.Serializer):
    name = serializers.CharField()
    penalty = serializers.IntegerField()
    message = serializers.CharField()
    data = serializers.SerializerMethodField()

    def get_data(self, obj:ConstraintError):
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
            if 'lesson_serializer' not in self.context:
                self.context['lesson_serializer'] = LessonReadSerializer(context=self.context)
            return self.context['lesson_serializer'].to_representation(instance)
        return fast_simple_serialize(instance)
    
class LessonErrorSerializer(serializers.Serializer):
    lesson = LessonReadSerializer()
    errors = ConstraintErrorSerializer(many=True)

    def get_lesson(self,obj):
        return fast_simple_serialize(obj)