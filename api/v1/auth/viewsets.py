from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import LoginResponseSerializer

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Check user/token authentication status.
        Returns the authenticated user's profile information."""
        user = request.user
        group = user.groups.first()

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": group.name if group else "Guest"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        """Logout the user and revoke tokens"""
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
           return Response(
               {"detail": "Refresh token is required"},
               status=status.HTTP_400_BAD_REQUEST
           )
        
        try:
            token = RefreshToken(refresh_token) 
            token.blacklist() # Revoke refresh token on logout
        except Exception:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)

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
        serializer = TokenObtainPairSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid email or password"},
                  status=status.HTTP_401_UNAUTHORIZED)
        
        # tokens = 

        return Response({
            "message": "Login successful",
            "data": serializer.validated_data
            },
            status=status.HTTP_200_OK)
        