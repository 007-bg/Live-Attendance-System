from rest_framework import serializers
from classes.models import Class


class StartAttendanceSerializer(serializers.Serializer):
    class_id = serializers.CharField()

    def validate_class_id(self, value):
        """Validate that the class exists."""
        try:
            Class.objects.get(id=value)
        except Class.DoesNotExist:
            raise serializers.ValidationError("Class not found")
        return value
