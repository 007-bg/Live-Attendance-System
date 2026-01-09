from django.shortcuts import render
from django.views import View
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.serializers.login import LoginSerializer
from users.serializers.user_read import UserReadSerializer
from users.serializers.user_write import UserWriteSerializer
from users.utils import (
    create_jwt_token,
)
from drf_spectacular.utils import extend_schema


class AuthViewSet(viewsets.ViewSet):
    """
    Authentication endpoints :
        - User registration
        - User login (jwt)
        - me
    """

    # --------------------
    # POST /api/auth/signup/
    # --------------------
    @extend_schema(
        request=UserWriteSerializer,
        responses={201: None},
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def signup(self, request):
        serializer = UserWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED,
        )

    # --------------------
    # POST /api/auth/login/
    # --------------------
    @extend_schema(
        request=LoginSerializer,
        responses={201: None},
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = create_jwt_token(user)
        return Response({"token": token}, status=status.HTTP_200_OK)

    # --------------------
    # GET /api/auth/me/
    # --------------------
    @extend_schema(
        responses={200: UserReadSerializer},
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserReadSerializer(request.user)
        return Response({"user": serializer.data}, status=status.HTTP_200_OK)
