from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from users.models import User


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom JWT authentication middleware for Django Channels WebSocket connections.
    Extracts JWT token from query parameters or headers, validates it, and adds user info to scope.
    """

    async def __call__(self, scope, receive, send):
        # Extract token from query parameters or headers
        token = self.get_token_from_scope(scope)

        if token:
            try:
                # Validate and decode the token
                access_token = AccessToken(token)
                user_id = access_token.get("user_id")

                # Fetch user from database
                user = await self.get_user(user_id)

                if user:
                    # Add user, user_id, and role to scope
                    scope["user"] = user
                    scope["user_id"] = user.id
                    scope["role"] = user.role
                else:
                    scope["user"] = AnonymousUser()
                    scope["user_id"] = None
                    scope["role"] = None

            except (InvalidToken, TokenError, KeyError):
                # Invalid token - set anonymous user
                scope["user"] = AnonymousUser()
                scope["user_id"] = None
                scope["role"] = None
        else:
            # No token provided - set anonymous user
            scope["user"] = AnonymousUser()
            scope["user_id"] = None
            scope["role"] = None

        return await super().__call__(scope, receive, send)

    def get_token_from_scope(self, scope):
        """
        Extract JWT token from WebSocket connection.
        First checks query parameters, then falls back to headers.

        Example WebSocket connection with token in query:
        ws://localhost:8000/ws/?token=your_jwt_token
        """
        # Try to get token from query parameters
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        if "token" in query_params:
            return query_params["token"][0]

        # Try to get token from headers (if provided)
        headers = dict(scope.get("headers", []))

        # Check for Authorization header
        if b"authorization" in headers:
            auth_header = headers[b"authorization"].decode("utf-8")
            # Expected format: "Bearer <token>"
            if auth_header.startswith("Bearer "):
                return auth_header.split(" ")[1]

        return None

    @database_sync_to_async
    def get_user(self, user_id):
        """
        Fetch user from database by ID.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
