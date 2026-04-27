from rest_framework import serializers

class ExcelUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class ValidationMeassageSerializer(serializers.Serializer):
    idx = serializers.ReadOnlyField()
    level = serializers.ReadOnlyField()
    field = serializers.ReadOnlyField()
    message = serializers.ReadOnlyField()