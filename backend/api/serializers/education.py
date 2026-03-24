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

class LessonGridSerializer(serializers.ModelSerializer):
    discipline_name = serializers.CharField(source='discipline.name', read_only=True)
    type_name = serializers.CharField(source='lesson_type.name', read_only=True)
    # Форматируем время в 24-часовой формат
    start = serializers.TimeField(source='timeslot.time_start', format='%H:%M')
    end = serializers.TimeField(source='timeslot.time_end', format='%H:%M')
    day = serializers.IntegerField(source='timeslot.day')
    order = serializers.IntegerField(source='timeslot.order_number')
    
    # Собираем названия групп и преподавателей в простые списки строк
    teachers_list = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name', source='teachers')
    groups_list = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name', source='study_groups')

    class Meta:
        model = Lesson
        fields = ['id', 'discipline_name', 'type_name', 'start', 'end', 'day', 'order', 'teachers_list', 'groups_list']
