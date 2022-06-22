from rest_framework import serializers


class LaunchProcessingSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=32)
    processing_time = serializers.IntegerField()


class ProcessingResultSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=32)
    result = serializers.CharField()
    processing_time = serializers.IntegerField()