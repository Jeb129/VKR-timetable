from rest_framework import serializers

class ConstraintOverrideSerializer(serializers.Serializer):
    name = serializers.CharField()
    weight = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)
    is_hard = serializers.BooleanField(required=False)

class StartGenerationSerializer(serializers.Serializer):
    constraints = ConstraintOverrideSerializer(many=True, required=False)
    time_limit = serializers.IntegerField(default=300, max_value=3600)
    num_workers = serializers.IntegerField(default=4, max_value=12)