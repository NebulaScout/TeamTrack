from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.exceptions import AuthenticationFailed, ValidationError



from .serializers import LoginResponseSerializer, CustomTokenObtainPairSerializer

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _success(self, data=None, message=None, status_code=status.HTTP_200_OK):
        payload = {"success": True}
        if message:
            payload["message"] = message
        if data is not None:
            payload["data"] = data
        return Response(payload, status_code)
    
    def _error(self, code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
        payload = {"success": False, "error": {"code": code, "message": message}}
        if details is not None:
            payload["error"]["details"] = details
        return Response(payload, status=status_code)

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[IsAuthenticated])
    def me(self, request):
        """Check user/token authentication status.
        Returns the authenticated user's profile information."""
        user = request.user
        group = user.groups.first()

        return self._success({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": group.name if group else "Guest"
        })

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        """Logout the user and revoke tokens"""
        refresh_token = request.data.get("refresh_token")

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
        