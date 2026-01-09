from rest_framework import serializers
from attendance_system.users.models import User
from rest_framework.validators import UniqueValidator


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role")
