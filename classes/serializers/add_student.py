from rest_framework import serializers
from classes.models import Class
from users.models import User


class AddStudentSerializer(serializers.Serializer):
    student_id = serializers.CharField()

    def validate_student_id(self, value):
        """Validate that the student exists and has student role."""
        try:
            student = User.objects.get(id=value, role=User.Role.STUDENT)
        except User.DoesNotExist:
            raise serializers.ValidationError("Student not found")
        return value
