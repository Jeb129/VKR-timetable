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
    user_name = serializers.ReadOnlyField(source='user.username')
    classroom_num = serializers.ReadOnlyField(source='classroom.num')

    class Meta:
        model = Booking
        fields = ['id', 'classroom', 'date_start', 'date_end', 'description', 'status']
        read_only_fields = ['user', 'status']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ScheduleAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleAdjustment
        fields = '__all__'

class ClassroomPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPreference
        fields = '__all__'


