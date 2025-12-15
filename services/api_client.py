import requests
from django.conf import settings

from utils.jwt import refresh_access_token

class APIClient:
    """Centralizes passing of headers to avoid code duplication in web views"""
    def __init__(self, request):
        self.request = request
        self.base_url = settings.BASE_URL.rstrip("/")

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        access_token = self.request.session.get('access_token')

        if not access_token:
            return {}
        
        headers["Authorization"] = f"Bearer {access_token}"
        
        return headers
    
    def _request(self, method, path, **kwargs):
        """ Make an HTTP request, attach auth headers, handle token refresh if needed, and return the response"""
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {}) # extract headers from the kwargs if available
        headers.update(self._get_headers()) # add authorization tokens to the headers
        response = requests.request(
            method,
            url,
            headers=headers,
            **kwargs
        )

        if response.status_code == 401:
            new_access_token = refresh_access_token(self.request)

            if not new_access_token:
                return response # handle missing auth tokens in caller method
            
            # Retry request with new access tokens
            headers["Authorization"] = f"Bearer {new_access_token}"
            response = requests.request(
                method,
                url,
                headers=headers,
                **kwargs
            )

        return response

    # Method calls
    def get(self, path, **kwargs):
        return self._request("GET", path, **kwargs)
    
    def post(self, path, **kwargs):
        return self._request("POST", path, **kwargs)
    
    def put(self, path, **kwargs):
        return self._request("PUT", path, **kwargs)
    
    def delete(self, path, **kwargs):
        return self._request("DELETE", path, **kwargs)