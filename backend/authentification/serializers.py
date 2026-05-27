from rest_framework import serializers
from authentification.models import CustomUser
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message="Пользователь с таким email уже существует.")]
    )
    
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )

    username = serializers.CharField(
        required=True,
        max_length=150
    )

    class Meta:
        model = CustomUser
        fields = ("email", "username", "password")

    def validate(self, attrs):
        return attrs

    def create(self, validated_data):
        # create_user автоматически захеширует пароль
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"]
        )
        return user

class CustomUserSerializer(serializers.ModelSerializer):
    is_internal = serializers.ReadOnlyField() # берется из @property модели
    is_moodle_linked = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            "username",
            'is_email_verified',
            'is_internal',
            'is_moodle_linked',
            'is_schedule_moderator',
            'is_booking_moderator',
            'is_staff',
        ]

    def get_is_moodle_linked(self, obj):
        return obj.moodle_id is not None