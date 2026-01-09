from rest_framework import serializers
from classes.models import Class
from users.serializers.user_read import UserReadSerializer


class ClassReadSerializer(serializers.ModelSerializer):
    teacher = UserReadSerializer(read_only=True)
    students = UserReadSerializer(many=True, read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = (
            "id",
            "class_name",
            "teacher",
            "students",
            "student_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_student_count(self, obj):
        return obj.students.count()
