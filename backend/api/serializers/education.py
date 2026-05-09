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
    draft_diffs = serializers.SerializerMethodField()
    draft_created = serializers.SerializerMethodField()

    def get_draft_diffs(self,obj):
        return (obj.draft_diffs if hasattr(obj, "draft_diffs") else [])
    
    def get_draft_created(self,obj):
        return hasattr(obj, "draft_created")

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
            "draft_diffs",
            "draft_created"
        ]