from rest_framework import serializers
from classes.models import Attendance
from users.serializers.user_read import UserReadSerializer


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for individual attendance records.
    """

    student = UserReadSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = ("id", "student", "status", "created_at")
        read_only_fields = ("id", "created_at")


class AttendanceSessionSerializer(serializers.Serializer):
    """
    Serializer for attendance session details.
    Groups attendance records by session_id.
    """

    session_id = serializers.CharField()
    date = serializers.DateTimeField()
    total_students = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    attendance_records = AttendanceRecordSerializer(many=True)
