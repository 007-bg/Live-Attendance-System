from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    ROLE_CHOICES = (
        (TEACHER, "Teacher"),
        (STUDENT, "Student"),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, db_index=True)
