from rest_framework import viewsets

# from .mixins import RegisterQueryMixin
from ..serializers import RegistrationSerializer
from ..models import RegisterModel

class RegisterViewSet(viewsets.ModelViewSet):
    queryset = RegisterModel.objects.all()
    serializer_class = RegistrationSerializer