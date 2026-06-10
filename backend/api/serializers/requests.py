from django.db import transaction
from django.db.models import Manager
from rest_framework import serializers

from api.models import (
    Booking,
    ClassroomPreference,
    ExcludedTimeslot,
    Request,
    ScheduleAdjustment,
    enums,
)
from config.utils import IdNameField, SimpleRelatedSerializer

# Связанные заявки


class ExcludedTimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcludedTimeslot
        fields = ["teacher", "timeslot"]


class ClassroomPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPreference
        fields = ["teacher", "discipline", "lesson_type", "classroom"]


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["classroom", "booking_type", "date_start", "date_end"]


class ScheduleAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleAdjustment
        fields = ["date", "lesson", "timeslot", "classroom"]


class ExcludedTimeslotReadSerializer(ExcludedTimeslotSerializer):
    teacher = SimpleRelatedSerializer(read_only=True)
    timeslot = serializers.StringRelatedField()


class ClassroomPreferenceReadSerializer(ClassroomPreferenceSerializer):
    teacher = SimpleRelatedSerializer(read_only=True)
    classroom = SimpleRelatedSerializer(read_only=True)
    discipline = serializers.StringRelatedField()
    lesson_type = serializers.StringRelatedField()


class BookingReadSerializer(BookingSerializer):
    classroom = SimpleRelatedSerializer(read_only=True)
    booking_type = serializers.StringRelatedField()


class ScheduleAdjustmentReadSerializer(ScheduleAdjustmentSerializer):
    lesson = serializers.StringRelatedField()
    timeslot = serializers.StringRelatedField()
    classroom = SimpleRelatedSerializer(read_only=True)


# Маппер, для удобства

TYPE_SERIALIZER_MAP = {
    enums.RequestType.EXCLUDED_TIMESLOT: {
        "model": ExcludedTimeslot,
        "write": ExcludedTimeslotSerializer,
        "read": ExcludedTimeslotReadSerializer,
    },
    enums.RequestType.CLASSROOM_PREFERENCE: {
        "model": ClassroomPreference,
        "write": ClassroomPreferenceSerializer,
        "read": ClassroomPreferenceReadSerializer,
    },
    enums.RequestType.BOOKING: {
        "model": Booking,
        "write": BookingSerializer,
        "read": BookingReadSerializer,
    },
    enums.RequestType.SCHEDULE_ADJUSTMENT: {
        "model": ScheduleAdjustment,
        "write": ScheduleAdjustmentSerializer,
        "read": ScheduleAdjustmentReadSerializer,
    },
}

# Поле для представления детаей заявки


class RequestDetailsField(serializers.Field):
    def to_representation(self, value):
        serializer_class = TYPE_SERIALIZER_MAP.get(value.type)["read"]
        child = value.get_child_obj
        return serializer_class(child, many=isinstance(child, Manager)).data

    def to_internal_value(self, data):
        """
        Валидация входящих данных
        """
        request_type = self.parent.initial_data.get("type")

        if request_type is None:
            raise serializers.ValidationError("Поле 'type' обязательно для заполнения.")

        try:
            request_type = int(request_type)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Некорректный формат 'type'.")

        serializer_class = TYPE_SERIALIZER_MAP.get(request_type)["write"]
        if not serializer_class:
            raise serializers.ValidationError(
                f"Для типа {request_type} валидатор не найден."
            )

        is_many = request_type == enums.RequestType.SCHEDULE_ADJUSTMENT
        sub_serializer = serializer_class(data=data, many=is_many, context=self.context)

        if sub_serializer.is_valid():
            return {"details": sub_serializer.validated_data}
        else:
            raise serializers.ValidationError(sub_serializer.errors)


class RequestSerializer(serializers.ModelSerializer):

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    type = IdNameField(choices=enums.RequestType.choices)
    status = IdNameField(choices=enums.RequestStatus.choices, read_only=True)

    details = RequestDetailsField(source="*")

    class Meta:
        model = Request
        fields = [
            "id",
            "user",
            "description",
            "status",
            "type",
            "admin_comment",
            "created_at",
            "details",
        ]
        read_only_fields = ["user", "status", "created_at"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Заменяем скрытое поле 'user' (или его отсутствие) на данные из короткого сериализатора
        ret["user"] = SimpleRelatedSerializer(instance.user).data
        return ret

    def create(self, validated_data):
        details_data = validated_data.pop("details")
        req_type = validated_data.get("type")
        user = validated_data.pop("user")

        with transaction.atomic():

            if req_type == enums.RequestType.SCHEDULE_ADJUSTMENT:
                base_request = Request.objects.create(user=user, **validated_data)
                adjustments = [
                    ScheduleAdjustment(request=base_request, **item)
                    for item in details_data
                ]
                ScheduleAdjustment.objects.bulk_create(adjustments)
                return base_request
            else:
                model = TYPE_SERIALIZER_MAP.get(req_type)["model"]
                return model.objects.create(user=user, **validated_data, **details_data)
