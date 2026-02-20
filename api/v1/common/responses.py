from rest_framework import status
from rest_framework.response import Response

class ResponseMixin:
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