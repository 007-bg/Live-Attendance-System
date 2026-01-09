import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from classes.redis_utils import (
    get_active_session,
    update_attendance as redis_update_attendance,
    clear_active_session,
    session_exists,
)
from classes.models import Class, Attendance
from users.models import User


class AttendanceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live attendance tracking.
    Handles real-time attendance marking, summary requests, and session completion.
    Uses Redis for session storage.
    """

    async def connect(self):
        """
        Handle WebSocket connection.
        JWT authentication is handled by JWTAuthMiddleware.
        User info is available in self.scope['user'], self.scope['user_id'], self.scope['role'].
        """
        # Get user info from scope (set by JWTAuthMiddleware)
        self.user_id = self.scope.get("user_id")
        self.role = self.scope.get("role")
        self.user = self.scope.get("user")

        # Check if user is authenticated
        if not self.user_id or self.user.is_anonymous:
            await self.accept()
            await self.send_error(
                "Authentication required. Please provide a valid JWT token."
            )
            await self.close()
            return

        # Join attendance group for broadcasting
        await self.channel_layer.group_add("attendance", self.channel_name)

        # Accept connection
        await self.accept()

        # Send connection success message with user info
        await self.send(
            text_data=json.dumps({
                "event": "CONNECTED",
                "data": {
                    "message": "WebSocket connection established",
                    "userId": self.user_id,
                    "role": self.role,
                },
            })
        )

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        # Leave attendance group
        await self.channel_layer.group_discard("attendance", self.channel_name)

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        Route to appropriate handlers based on event type.
        """
        try:
            data = json.loads(text_data)
            event = data.get("event")
            payload = data.get("data", {})

            if event == "ATTENDANCE_MARKED":
                await self.handle_attendance_marked(payload)
            elif event == "TODAY_SUMMARY":
                await self.handle_today_summary(payload)
            elif event == "MY_ATTENDANCE":
                await self.handle_my_attendance(payload)
            elif event == "DONE":
                await self.handle_done(payload)
            else:
                await self.send_error(f"Unknown event: {event}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(str(e))

    async def handle_attendance_marked(self, payload):
        """
        Handle ATTENDANCE_MARKED event.
        Teacher marks a student's attendance.
        """
        # Verify teacher role
        if self.role != "TEACHER":
            await self.send_error("Only teachers can mark attendance")
            return

        class_id = payload.get("classId")
        student_id = payload.get("studentId")
        attendance_status = payload.get("status")

        if not class_id or not student_id or not attendance_status:
            await self.send_error("Missing classId, studentId or status")
            return

        # Check if active session exists for this class
        if not await sync_to_async(session_exists)(class_id):
            await self.send_error("No active attendance session for this class")
            return

        # Update session in Redis
        await sync_to_async(redis_update_attendance)(
            class_id, student_id, attendance_status
        )

        # Broadcast to all connected clients via channel layer
        await self.channel_layer.group_send(
            "attendance",
            {
                "type": "attendance_broadcast",
                "event": "ATTENDANCE_MARKED",
                "data": {
                    "classId": class_id,
                    "studentId": student_id,
                    "status": attendance_status,
                },
            },
        )

    async def handle_today_summary(self, payload):
        """
        Handle TODAY_SUMMARY event.
        Calculate and broadcast attendance summary.
        """
        # Verify teacher role
        if self.role != "TEACHER":
            await self.send_error("Only teachers can request attendance summary")
            return

        class_id = payload.get("classId")

        if not class_id:
            await self.send_error("Class ID required")
            return

        session = await sync_to_async(get_active_session)(class_id)
        if not session:
            await self.send_error("No active attendance session for this class")
            return

        attendance = session.get("attendance", {})
        present = sum(1 for status in attendance.values() if status == "present")
        absent = sum(1 for status in attendance.values() if status == "absent")
        total = len(attendance)

        # Broadcast to all connected clients
        await self.channel_layer.group_send(
            "attendance",
            {
                "type": "attendance_broadcast",
                "event": "TODAY_SUMMARY",
                "data": {
                    "classId": class_id,
                    "present": present,
                    "absent": absent,
                    "total": total,
                },
            },
        )

    async def handle_my_attendance(self, payload):
        """
        Handle MY_ATTENDANCE event.
        Student requests their own attendance status.
        """
        # Verify student role
        if self.role != "STUDENT":
            await self.send_error("Only students can request their own attendance")
            return

        class_id = payload.get("classId")
        student_id = str(self.user_id)  # Get from JWT (scope)

        if not class_id:
            await self.send_error("Class ID required")
            return

        session = await sync_to_async(get_active_session)(class_id)
        if not session:
            await self.send(
                text_data=json.dumps({
                    "event": "MY_ATTENDANCE",
                    "data": {"status": "not yet updated"},
                })
            )
            return

        student_status = session.get("attendance", {}).get(
            student_id, "not yet updated"
        )

        await self.send(
            text_data=json.dumps({
                "event": "MY_ATTENDANCE",
                "data": {"status": student_status},
            })
        )

    async def handle_done(self, payload):
        """
        Handle DONE event.
        Persist attendance to database and clear session.
        """
        # Verify teacher role
        if self.role != "TEACHER":
            await self.send_error("Only teachers can end attendance session")
            return

        class_id = payload.get("classId")

        if not class_id:
            await self.send_error("Class ID required")
            return

        session = await sync_to_async(get_active_session)(class_id)
        if not session:
            await self.send_error("No active attendance session for this class")
            return

        # Persist to database
        summary = await self.persist_attendance(session)

        if summary is None:
            await self.send_error("Failed to persist attendance")
            return

        # Clear session from Redis
        await sync_to_async(clear_active_session)(class_id)

        # Broadcast to all connected clients
        await self.channel_layer.group_send(
            "attendance",
            {
                "type": "attendance_broadcast",
                "event": "DONE",
                "data": {
                    "classId": class_id,
                    "message": "Attendance persisted",
                    "present": summary["present"],
                    "absent": summary["absent"],
                    "total": summary["total"],
                },
            },
        )

    @database_sync_to_async
    def persist_attendance(self, session):
        """
        Persist attendance records to database.
        """
        session_id = session.get("sessionId")
        class_id = session.get("classId")
        attendance_dict = session.get("attendance", {})

        try:
            class_instance = Class.objects.get(id=class_id)

            # Get all enrolled students
            enrolled_students = class_instance.students.all()

            # Mark all unmarked students as absent
            for student in enrolled_students:
                student_id_str = str(student.id)
                if student_id_str not in attendance_dict:
                    attendance_dict[student_id_str] = "absent"

            # Create attendance records
            for student_id_str, status in attendance_dict.items():
                try:
                    student = User.objects.get(id=student_id_str)
                    Attendance.objects.create(
                        session_id=session_id,
                        class_instance=class_instance,
                        student=student,
                        status=status,
                    )
                except User.DoesNotExist:
                    continue

            # Calculate summary
            present = sum(1 for s in attendance_dict.values() if s == "present")
            absent = sum(1 for s in attendance_dict.values() if s == "absent")
            total = len(attendance_dict)

            return {"present": present, "absent": absent, "total": total}
        except Class.DoesNotExist:
            return None

    async def attendance_broadcast(self, event):
        """
        Handler for broadcasting messages to all clients in the group.
        """
        await self.send(
            text_data=json.dumps({"event": event["event"], "data": event["data"]})
        )

    async def send_error(self, message):
        """
        Send error message to client.
        """
        await self.send(
            text_data=json.dumps({"event": "ERROR", "data": {"message": message}})
        )
