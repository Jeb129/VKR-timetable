from rest_framework import serializers
from api.models import (
    Institute,
    StudyProgram,
    StudyGroup,
    Teacher,
    AcademicLoad,
    Timeslot,
    Lesson,
)
from config.utils import SimpleRelatedSerializer

from django.forms.models import model_to_dict


class InstituteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institute
        fields = "__all__"


class StudyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyProgram
        fields = "__all__"


class StudyGroupSerializer(serializers.ModelSerializer):
    sub_groups = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )

    class Meta:
        model = StudyGroup
        fields = "__all__"


class AcademicLoadSerializer(serializers.ModelSerializer):
    discipline_name = serializers.ReadOnlyField(source="discipline.name")
    teacher_name = serializers.ReadOnlyField(source="teacher.name")
    group_name = serializers.ReadOnlyField(source="study_group.name")

    class Meta:
        model = AcademicLoad
        fields = "__all__"
        read_only_fields=["id"]


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = "__all__"


class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = "__all__"

# Чисто на всякий случай мало ли будем создавать объекты не через админку
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"
        

# сериализатор только для чтения.
# для всех M2M полей возвращается id объекта и наименование
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
                "was": SimpleRelatedSerializer(old_obj,many=is_list).data,
                "now": SimpleRelatedSerializer(current_val,many=is_list).data
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