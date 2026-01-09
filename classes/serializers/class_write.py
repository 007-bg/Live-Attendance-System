from rest_framework import serializers
from classes.models import Class


class ClassWriteSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(max_length=255)

    class Meta:
        model = Class
        fields = ("class_name",)

    def create(self, validated_data):
        # Automatically assign the authenticated user as the teacher
        user = self.context["request"].user

        # Verify the user is a teacher
        if user.role != "TEACHER":
            raise serializers.ValidationError("Only teachers can create classes.")

        validated_data["teacher"] = user
        class_instance = Class.objects.create(**validated_data)
        return class_instance
