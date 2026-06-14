from rest_framework import serializers
from api.models import *


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
    discipline = serializers.ReadOnlyField(source="discipline.name")
    teacher = serializers.ReadOnlyField(source="teacher.name")
    group = serializers.ReadOnlyField(source="study_group.name")

    class Meta:
        model = AcademicLoad
        fields = "__all__"
        read_only_fields = ["id"]

class PlannedLessonSerializer(serializers.ModelSerializer):
    discipline = serializers.ReadOnlyField(source="discipline.name")
    lesson_type = serializers.ReadOnlyField(source="lesson_type.short_name")

    class Meta:
        model = AcademicLoad
        fields = "__all__"
        read_only_fields = ["id"]

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = "__all__"


class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = "__all__"


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = "__all__"


class LessonTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonType
        fields = "__all__"


class ScheduleScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleScenario
        fields = "__all__"

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = "__all__"


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "name", "address", "work_start_time", "work_end_time"]


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"


class BookingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingType
        fields = ["id", "name"]


class BuildingTravelTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingTravelTime
        fields = "__all__"


class ConstraintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraint
        fields = "__all__"

class ClassroomPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPreference
        fields = "__all__"

class ClassroomSerializer(serializers.ModelSerializer):
    building = BuildingSerializer(read_only=True)

    class Meta:
        model = Classroom
        fields = [
            "id",
            "building",
            "num",
            "name",
            "capacity",
        ]
