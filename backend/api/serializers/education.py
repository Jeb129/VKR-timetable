from rest_framework import serializers
from ..models.models import (
    Institute, StudyProgram, StudyGroup, Discipline, 
    LessonType, Teacher, Timeslot, Lesson
)

class InstituteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institute
        fields = '__all__'

class StudyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyProgram
        fields = '__all__'

class StudyGroupSerializer(serializers.ModelSerializer):
    sub_groups = serializers.SlugRelatedField(
        many=True, 
        read_only=True, 
        slug_field='name'
    )

    class Meta:
        model = StudyGroup
        fields = '__all__'
class AcademicLoadSerializer(serializers.ModelSerializer):
    discipline_name = serializers.ReadOnlyField(source='discipline.name')
    teacher_name = serializers.ReadOnlyField(source='teacher.name')
    group_name = serializers.ReadOnlyField(source='study_group.name')

    class Meta:
        model = AcademicLoad
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'weight', 'user']

class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    discipline_name = serializers.ReadOnlyField(source='discipline.name')
    lesson_type_name = serializers.ReadOnlyField(source='lesson_type.name')
    classroom_name = serializers.ReadOnlyField(source='classroom.name')
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'discipline', 'discipline_name', 'lesson_type', 
            'lesson_type_name', 'timeslot', 'classroom', 
            'classroom_name', 'teachers', 'study_groups'
        ]
