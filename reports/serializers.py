from rest_framework import serializers

class ReportSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    location = serializers.DictField()
    image_url = serializers.URLField()
    status = serializers.CharField(default="pending")
