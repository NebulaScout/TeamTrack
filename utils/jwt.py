import requests
from django.conf import settings

def refresh_access_token(request):
    """ Refresh access token on expiry"""
    refresh_token = request.session.get("refresh_token")

    if not refresh_token:
        return None
    
    api_url = f"{settings.BASE_URL}/api/token/refresh/"
    data = {"refresh": refresh_token}

    try:
        response = requests.post(api_url, json=data)
        response.raise_for_status() # raise http error for 400/500 status codes

        new_access = response.json().get("access")
        request.session["access_token"] = new_access

        return new_access

    except requests.exceptions.HTTPError as e:
        return None
    
    except requests.exceptions.RequestException as e:
        return None
