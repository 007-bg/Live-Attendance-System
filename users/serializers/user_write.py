from rest_framework import serializers
from users.models import User
from rest_framework.validators import UniqueValidator


class UserWriteSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "role")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            # create_user usually handles password hashing, but we support creating without one
            user.set_unusable_password()
        user.save()
        return user
