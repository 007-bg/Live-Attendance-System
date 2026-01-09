from django.contrib.auth import authenticate
from rest_framework import serializers
from attendance_system.users.models import User
from rest_framework.validators import UniqueValidator


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")

        attrs["user"] = user
        return attrs
