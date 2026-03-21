from rest_framework import serializers
from authentification.models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    name = serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ("email", "name", "password")

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            email=validated_data["email"],
            username=validated_data["name"],
            password=validated_data["password"]
        )