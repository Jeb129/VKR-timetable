from rest_framework import serializers
from django.utils import timezone
from api.models import (
    Request,
    ExcludedTimeslot,
    ClassroomPreference,
    Booking,
    ScheduleAdjustment,
    Constraint,
    enums
)


class ConstraintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Constraint
        fields = "__all__"


class RequestBaseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_full_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Request
        fields = [
            "id",
            "user",
            "user_full_name",
            "description",
            "created_at",
            "status",
            "status_display",
        ]


class BookingSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source="user.username")
    classroom_num = serializers.ReadOnlyField(source="classroom.num")

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "user_name",
            "classroom",
            "classroom_num",
            "date_start",
            "date_end",
            "description",
            "status",
            "admin_comment",
        ]
        read_only_fields = ["id", "user", "user_name", "classroom_num"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
    
    def validate(self,data):
        start = data['date_start']
        end = data['date_end']
        classroom = data['classroom']

        # 1. Проверка: Конец не может быть раньше начала
        if start >= end:
            raise serializers.ValidationError("Время начала должно быть строго меньше времени окончания.")

        # 2. Проверка: Бронирование в прошлом
        if start < timezone.now():
             raise serializers.ValidationError("Нельзя бронировать аудиторию на прошедшее время.")

        # 3. Проверка наложений на другие ОДОБРЕННЫЕ брони
        overlapping_bookings = Booking.objects.filter(
            classroom=classroom,
            status=enums.RequestStatus.VERIFIED,
            date_start__lt=end,
            date_end__gt=start
        )
        if overlapping_bookings.exists():
            raise serializers.ValidationError("Аудитория уже забронирована на это время.")

        # 4. Проверка наложений на расписание (Lesson)
        # Находим день недели и четность для даты начала
        day_of_week = start.weekday() + 1
        week_num = 1 if start.isocalendar()[1] % 2 != 0 else 2
        
        # Ищем уроки в этой аудитории, которые пересекаются по времени
        # (Сравниваем время внутри DateTime с временем в Timeslot)
        overlapping_lessons = Lesson.objects.filter(
            classroom=classroom,
            timeslot__day=day_of_week,
            timeslot__week_num=week_num,
            scenario__is_active=True,
            timeslot__time_start__lt=end.time(),
            timeslot__time_end__gt=start.time()
        )
        
        if overlapping_lessons.exists():
            raise serializers.ValidationError("В это время в аудитории проходит учебное занятие по расписанию.")

        return data


class ScheduleAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleAdjustment
        fields = "__all__"


class ClassroomPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPreference
        fields = "__all__"
