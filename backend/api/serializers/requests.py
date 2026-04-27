from rest_framework import serializers
from django.utils import timezone
from api.models import (
    Request,
    ExcludedTimeslot,
    ClassroomPreference,
    Booking,
    ScheduleAdjustment,
    Constraint,
    Lesson,
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
    
    def validate(self, data):
        instance = self.instance
        start = data.get('date_start', getattr(instance, 'date_start', None))
        end = data.get('date_end', getattr(instance, 'date_end', None))
        classroom = data.get('classroom', getattr(instance, 'classroom', None))

        # Если статус меняется на "Отклонено", пропускаем сложные проверки наложений
        if data.get('status') == 2: 
            return data

        # Проверка логики времени 
        if start and end:
            if start >= end:
                raise serializers.ValidationError("Время начала должно быть меньше времени окончания.")
            
            # Проверка наложений (только при создании или изменении времени/аудитории)
            # Чтобы не ругаться на саму себя при обновлении, исключаем текущий ID
            exclude_id = instance.id if instance else None
            
            # 1. Проверка на другие брони
            if Booking.objects.filter(
                classroom=classroom,
                status=1, # VERIFIED
                date_start__lt=end,
                date_end__gt=start
            ).exclude(id=exclude_id).exists():
                raise serializers.ValidationError("Аудитория уже занята другой бронью.")

            # 2. Проверка на учебные пары
            day_of_week = start.weekday() + 1
            week_num = 1 if start.isocalendar()[1] % 2 != 0 else 2
            
            if Lesson.objects.filter(
                classroom=classroom,
                timeslot__day=day_of_week,
                timeslot__week_num=week_num,
                scenario__is_active=True,
                timeslot__time_start__lt=end.time(),
                timeslot__time_end__gt=start.time()
            ).exists():
                raise serializers.ValidationError("В это время в аудитории занятие по расписанию.")

        return data


class ScheduleAdjustmentSerializer(serializers.ModelSerializer):
    # текстовые поля для удобства админа
    user_name = serializers.ReadOnlyField(source="user.username")
    lesson_name = serializers.ReadOnlyField(source="lesson.discipline.name")
    teacher_name = serializers.ReadOnlyField(source="user.teacher.name")
    # Информация о новом слоте
    new_time = serializers.ReadOnlyField(source="timeslot.time_start")
    new_order = serializers.ReadOnlyField(source="timeslot.order_number")
    # Информация о старом слоте 
    old_time = serializers.ReadOnlyField(source="lesson.timeslot.time_start")
    old_day = serializers.ReadOnlyField(source="lesson.timeslot.day")
    class Meta:
        model = ScheduleAdjustment
        fields = [
            "id", "user", "user_name", "teacher_name", "lesson", "lesson_name",
            "date", "timeslot", "new_time", "new_order", "old_time", "old_day",
            "description", "status", "admin_comment"
        ]
        read_only_fields = ["id", "user"]


class ClassroomPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPreference
        fields = "__all__"
