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
