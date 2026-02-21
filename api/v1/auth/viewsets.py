from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from api.v1.common.responses import ResponseMixin
from .serializers import LoginResponseSerializer, CustomTokenObtainPairSerializer

class AuthViewSet(ResponseMixin, viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[IsAuthenticated])
    def me(self, request):
        """Check user/token authentication status.
        Returns the authenticated user's profile information."""
        user = request.user
        group = user.groups.first()

        # get avatar url
        avatar_url = None
        if hasattr(user, "profile") and user.profile.avatar:
            avatar_url = request.build_absolute_uri(user.profile.avatar.url)

        return self._success({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": avatar_url,
            "role": group.name if group else "Guest"
        })

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        """Logout the user and revoke tokens"""
        refresh_token = request.data.get("refresh_token") #TODO: fix logout issue

        if not refresh_token:
           return self._error(
               "VALIDATION_ERROR",
               "Invalid Input",
               {"refresh_token": ["Refresh token is required"]},
               status.HTTP_400_BAD_REQUEST,
           )
        
        try:
            token = RefreshToken(refresh_token) 
            token.blacklist() # Revoke refresh token on logout
        except Exception:
            return self._error(
                "INVALID_TOKEN",
                "Invalid token",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        
        return self._success(message="Logged out successfully")

    @extend_schema(
        summary="User login",
        description="Authenticate user credentials and return JWT tokens",
        request=TokenObtainPairSerializer,
        responses={
            200: LoginResponseSerializer,
            401: OpenApiResponse(description="Invalid email or password"),
            429: OpenApiResponse(description="Too many login attempts"),
        },
    )
    @action(
        detail=False,
        methods=['post'], 
        url_path="login", 
        permission_classes=[AllowAny], 
        # throttle_classes=[AnonRateThrottle]
    )
    def login(self, request):
        """Authenticate user and generate tokens"""
        serializer = CustomTokenObtainPairSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            return self._error(
            "AUTHENTICATION_FAILED",
            "Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        except ValidationError as exc:
            return self._error(
                "VALIDATION_ERROR",
                "Invalid input",
                exc.detail,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        

        return self._success(
            message="Login successful",
            data=serializer.validated_data,
            )
        