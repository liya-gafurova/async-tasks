from rest_framework import serializers


class LaunchProcessingSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=20)
    processing_time = serializers.IntegerField()
