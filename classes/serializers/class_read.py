from rest_framework import serializers
from classes.models import Class, Attendance
from users.serializers.user_read import UserReadSerializer
from django.db.models import Count, Q


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


class ClassDetailSerializer(serializers.ModelSerializer):
    """
    Detailed class serializer including students and all attendance sessions.
    """

    teacher = UserReadSerializer(read_only=True)
    students = UserReadSerializer(many=True, read_only=True)
    student_count = serializers.SerializerMethodField()
    sessions = serializers.SerializerMethodField()
    total_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = (
            "id",
            "class_name",
            "teacher",
            "students",
            "student_count",
            "total_sessions",
            "sessions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_student_count(self, obj):
        return obj.students.count()

    def get_total_sessions(self, obj):
        """Get total number of unique attendance sessions."""
        return (
            Attendance.objects.filter(class_instance=obj)
            .values("session_id")
            .distinct()
            .count()
        )

    def get_sessions(self, obj):
        """Get all attendance sessions with their details."""
        # Get all unique session IDs for this class
        session_ids = (
            Attendance.objects.filter(class_instance=obj)
            .values_list("session_id", flat=True)
            .distinct()
            .order_by("-session_id")
        )

        sessions = []
        for session_id in session_ids:
            # Get all attendance records for this session
            attendance_records = Attendance.objects.filter(
                class_instance=obj, session_id=session_id
            ).select_related("student")

            # Calculate statistics
            total_students = attendance_records.count()
            present_count = attendance_records.filter(
                status=Attendance.Status.PRESENT
            ).count()
            absent_count = attendance_records.filter(
                status=Attendance.Status.ABSENT
            ).count()

            # Get the date from the first record
            first_record = attendance_records.first()
            session_date = first_record.created_at if first_record else None

            # Serialize attendance records
            attendance_data = [
                {
                    "id": record.id,
                    "student": UserReadSerializer(record.student).data,
                    "status": record.status,
                    "created_at": record.created_at,
                }
                for record in attendance_records
            ]

            sessions.append({
                "session_id": session_id,
                "date": session_date,
                "total_students": total_students,
                "present_count": present_count,
                "absent_count": absent_count,
                "attendance_records": attendance_data,
            })

        return sessions
