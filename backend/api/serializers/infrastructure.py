from rest_framework import serializers
from .models import Building, Equipment, Classroom

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'

class ClassroomSerializer(serializers.ModelSerializer):
    building_details = BuildingSerializer(source='building', read_only=True)

    class Meta:
        model = Classroom
        fields = ['id', 'building', 'building_details', 'num', 'name', 'capacity']

