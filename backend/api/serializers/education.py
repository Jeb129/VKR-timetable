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


class LessonSerializer(serializers.ModelSerializer):
    # Текстовые названия из связанных моделей
    discipline_name = serializers.ReadOnlyField(source="discipline.name")
    type_name = serializers.ReadOnlyField(source="lesson_type.name")
    classroom_name = serializers.ReadOnlyField(source="classroom.name")

    # Номер пары и день для сортировки
    order = serializers.ReadOnlyField(source="timeslot.order_number")
    day = serializers.ReadOnlyField(source="timeslot.day")
    week_num = serializers.ReadOnlyField(source='timeslot.week_num') 

    # Списки имен преподавателей и групп (Many-to-Many)
    teachers_list = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name", source="teachers"
    )
    groups_list = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name", source="study_groups"
    )

    class Meta:
        model = Lesson
        fields = [
            "id",
            "discipline_name",
            "type_name",
            "classroom_name",
            "timeslot",
            "order",
            "day",
            "week_num",
            "teachers_list",
            "groups_list",
            "classroom",
            "scenario",  # Оставляем ID для фильтрации
        ]
