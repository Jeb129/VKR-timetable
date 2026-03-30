from rest_framework import serializers
from ..models.models import Building,BuildingTravelTime, Equipment, Classroom

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'

class BuildingTravelTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingTravelTime
        fields = '__all__'

class ClassroomSerializer(serializers.ModelSerializer):
    building_details = BuildingSerializer(source='building', read_only=True)
    work_start = serializers.TimeField(source='building.work_start_time', read_only=True)
    work_end = serializers.TimeField(source='building.work_end_time', read_only=True)

    class Meta:
        model = Classroom
        fields = ['id', 'building', 'building_details', 'num', 'name', 'work_start', 'work_end', 'capacity']

