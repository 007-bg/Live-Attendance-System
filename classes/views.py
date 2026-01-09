from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from datetime import datetime
import uuid
from classes.models import Class, Attendance
from classes.serializers import (
    ClassWriteSerializer,
    ClassReadSerializer,
    ClassDetailSerializer,
    AddStudentSerializer,
    StartAttendanceSerializer,
)
from users.models import User
from classes.redis_utils import (
    set_active_session,
    get_active_session,
    update_attendance,
    clear_active_session,
    session_exists,
)


class IsTeacher(IsAuthenticated):
    """
    Custom permission to only allow teachers to access.
    """

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == User.Role.TEACHER
        )


class IsStudent(IsAuthenticated):
    """
    Custom permission to only allow students to access.
    """

    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role == User.Role.STUDENT
        )


class ClassViewSet(viewsets.ViewSet):
    """
    ViewSet for managing classes.
    All endpoints use @action decorators with explicit permissions.
    """

    @extend_schema(
        responses={
            200: ClassReadSerializer(many=True),
        },
        description="List all classes. Teachers see classes they teach, students see classes they're enrolled in, admins see all classes.",
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def list_classes(self, request):
        """
        GET /api/class/list_classes/
        List all classes based on user role.
        - Teachers: Classes they teach
        - Students: Classes they're enrolled in
        - Admins: All classes
        """
        user = request.user

        if user.role == User.Role.TEACHER:
            # Teachers see classes they teach
            classes = Class.objects.filter(teacher=user).prefetch_related(
                "students", "teacher"
            )
        elif user.role == User.Role.STUDENT:
            # Students see classes they're enrolled in
            classes = Class.objects.filter(students=user).prefetch_related(
                "students", "teacher"
            )
        elif user.role == User.Role.ADMIN:
            # Admins see all classes
            classes = Class.objects.all().prefetch_related("students", "teacher")
        else:
            classes = Class.objects.none()

        serializer = ClassReadSerializer(classes, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ClassWriteSerializer,
        responses={201: ClassReadSerializer},
        description="Create a new class. Teacher is automatically assigned from authenticated user.",
    )
    @action(detail=False, methods=["post"], permission_classes=[IsTeacher])
    def create_class(self, request):
        """
        POST /api/class/create_class/
        Create a new class. Teacher is automatically assigned from authenticated user.
        """
        serializer = ClassWriteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        class_instance = serializer.save()

        # Return the created class with read serializer
        read_serializer = ClassReadSerializer(class_instance)
        return Response(
            {"success": True, "data": read_serializer.data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=AddStudentSerializer,
        responses={
            200: ClassReadSerializer,
            403: OpenApiResponse(description="Forbidden, not class teacher"),
            404: OpenApiResponse(description="Class not found or Student not found"),
        },
        description="Add a student to the class. Only the teacher who owns the class can add students.",
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="add-student",
        permission_classes=[IsTeacher],
    )
    def add_student(self, request, pk=None):
        """
        POST /api/class/:id/add-student/
        Add a student to the class. Only the teacher who owns the class can add students.
        """
        class_instance = get_object_or_404(Class, pk=pk)

        # Check if the requesting teacher owns this class
        if class_instance.teacher != request.user:
            return Response(
                {"success": False, "error": "Forbidden, not class teacher"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AddStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = get_object_or_404(User, id=serializer.validated_data["student_id"])

        # Add student to class
        class_instance.students.add(student)

        # Return updated class
        read_serializer = ClassReadSerializer(class_instance)
        return Response(
            {"success": True, "data": read_serializer.data}, status=status.HTTP_200_OK
        )

    @extend_schema(
        responses={
            200: ClassDetailSerializer,
            403: OpenApiResponse(
                description="Forbidden, not class teacher or enrolled student"
            ),
            404: OpenApiResponse(description="Class not found"),
        },
        description="Get class details including all students and attendance sessions by class name. Accessible by teacher (owner) or enrolled students.",
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="get-class/(?P<class_name>[^/.]+)",
    )
    def get_class(self, request, class_name=None):
        """
        GET /api/class/get-class/:class_name/
        Get class details including all students and attendance sessions by class name.
        Accessible by teacher (owner) or enrolled students.
        """
        class_instance = get_object_or_404(Class, class_name=class_name)

        # Check access: teacher owns class OR student is enrolled
        is_teacher = (
            request.user.role == User.Role.TEACHER
            and class_instance.teacher == request.user
        )
        is_enrolled_student = (
            request.user.role == User.Role.STUDENT
            and class_instance.students.filter(id=request.user.id).exists()
        )

        if not (is_teacher or is_enrolled_student):
            return Response(
                {
                    "success": False,
                    "error": "Forbidden, not class teacher or enrolled student",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ClassDetailSerializer(class_instance)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Returns attendance status for the student. Status can be 'present', 'absent', or null if not yet marked."
            ),
            403: OpenApiResponse(description="Forbidden, not enrolled in class"),
            404: OpenApiResponse(description="Class not found"),
        },
        description="Get student's own attendance for a class. Student must be enrolled.",
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="my-attendance",
        permission_classes=[IsStudent],
    )
    def my_attendance(self, request, pk=None):
        """
        GET /api/class/:id/my-attendance/
        Get student's own attendance for a class. Student must be enrolled.
        """
        class_instance = get_object_or_404(Class, pk=pk)

        # Check if student is enrolled in this class
        if not class_instance.students.filter(id=request.user.id).exists():
            return Response(
                {"success": False, "error": "Forbidden, not enrolled in class"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if attendance record exists
        try:
            attendance = Attendance.objects.get(
                class_instance=class_instance, student=request.user
            )
            return Response(
                {
                    "success": True,
                    "data": {
                        "classId": str(class_instance.id),
                        "status": attendance.status,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Attendance.DoesNotExist:
            return Response(
                {
                    "success": True,
                    "data": {"classId": str(class_instance.id), "status": None},
                },
                status=status.HTTP_200_OK,
            )

    @extend_schema(
        request=StartAttendanceSerializer,
        responses={
            200: OpenApiResponse(
                description="Attendance session started successfully",
                response={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "sessionId": {"type": "string"},
                                "classId": {"type": "string"},
                                "startedAt": {"type": "string"},
                            },
                        },
                    },
                },
            ),
            403: OpenApiResponse(description="Forbidden, not class teacher"),
            404: OpenApiResponse(description="Class not found"),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsTeacher],
        url_path="start-attendance",
    )
    def start_attendance(self, request):
        """
        Start an attendance session for a class.
        Only the teacher who owns the class can start attendance.
        """
        serializer = StartAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        class_id = serializer.validated_data["class_id"]

        # Get the class instance
        try:
            class_instance = Class.objects.get(id=class_id)
        except Class.DoesNotExist:
            return Response(
                {"success": False, "error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify teacher owns the class
        if class_instance.teacher != request.user:
            return Response(
                {"success": False, "error": "Forbidden, not class teacher"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if session already exists for this class
        if session_exists(str(class_id)):
            return Response(
                {
                    "success": False,
                    "error": "Active session already exists for this class",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create session data
        session_id = str(uuid.uuid4())
        session_data = {
            "sessionId": session_id,
            "classId": str(class_id),
            "startedAt": datetime.now().isoformat(),
            "attendance": {},
        }

        # Store in Redis (class-specific)
        set_active_session(str(class_id), session_data)

        return Response(
            {
                "success": True,
                "data": {
                    "sessionId": session_id,
                    "classId": str(class_id),
                    "startedAt": session_data["startedAt"],
                },
            },
            status=status.HTTP_200_OK,
        )
