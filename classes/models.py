from django.db import models
from users.models import User


class Class(models.Model):
    """
    Represents a class/course with a teacher and enrolled students.
    """

    class_name = models.CharField(max_length=255)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="classes_taught",
        limit_choices_to={"role": "teacher"},
    )
    students = models.ManyToManyField(
        User,
        related_name="classes_enrolled",
        limit_choices_to={"role": "student"},
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ["class_name"]

    def __str__(self):
        return f"{self.class_name} (Teacher: {self.teacher.username})"


class Attendance(models.Model):
    """
    Represents attendance records for students in classes.
    """

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"

    session_id = models.CharField(max_length=255, db_index=True)
    class_instance = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name="attendance_records"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        limit_choices_to={"role": "student"},
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
        unique_together = [["session_id", "student"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.username} - {self.class_instance.class_name} - {self.status} (Session: {self.session_id})"
