from django.core.management.base import BaseCommand

from core.services.roles import initialize_roles

class Command(BaseCommand):
    help = "Initialize default roles and permissions"

    def handle(self, *args, **kwargs):
        initialize_roles()
        self.stdout.write(self.style.SUCCESS("Roles initialized"))