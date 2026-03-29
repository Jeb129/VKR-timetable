from rest_framework import serializers
from api.models import (
    Request, ExcludedTimeslot, ClassroomPreference, 
    Booking, ScheduleAdjustment, Constraint
)

class ConstraintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraint
        fields = '__all__'

class RequestBaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Request
        fields = ['id', 'user', 'user_full_name', 'description', 'created_at', 'status', 'status_display']

class BookingSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Booking
        fields = '__all__'

class ScheduleAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleAdjustment
        fields = '__all__'

class ClassroomPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPreference
        fields = '__all__'


