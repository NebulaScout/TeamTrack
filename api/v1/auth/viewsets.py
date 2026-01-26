from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

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
        """Create a POST endpoint called /logout/ on this ViewSet, that's not tied to any object ID."""
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