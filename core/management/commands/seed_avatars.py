import requests
import hashlib
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db.models import Q

from django.contrib.auth.models import User
from accounts.models import UserProfile

# Avatar sources
AVATAR_SOURCES = [
   "https://api.dicebear.com/7.x/avataaars/png?seed={seed}",
    "https://api.dicebear.com/7.x/bottts/png?seed={seed}",
    "https://api.dicebear.com/7.x/personas/png?seed={seed}",
    "https://i.pravatar.cc/300?u={seed}",
    "https://robohash.org/{seed}.png?size=300x300", 
]

class Command(BaseCommand):
    help = "Seed avatars for users without profile pictures"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=50)
        parser.add_argument("--source", type=int, default=0)

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        source_index = options["source"]

        self.stdout.write(self.style.SUCCESS("Starting avatar seeding..."))

        users_with_avatar = User.objects.filter(profile__avatar__isnull=False).exclude(profile__avatar="")
        users_without_avatar = User.objects.filter(Q(profile__avatar__isnull=True) | Q(profile__avatar=""))

        self.stdout.write(f"\nUsers with avatars: {users_with_avatar.count()}")
        self.stdout.write(f"Users without avatars: {users_without_avatar.count()}")

        users = users_without_avatar[:batch_size]

        if not users:
            self.stdout.write("No users need avatars.")
            return
        
        for i, user in enumerate(users, 1):
            seed = hashlib.md5(user.email.encode()).hexdigest()
            source_url = AVATAR_SOURCES[
                (source_index + i) % len(AVATAR_SOURCES)
            ].format(seed=seed)

            try:
                response = requests.get(source_url, timeout=10)
                response.raise_for_status()

                filename = f"avatar_{user.id}_{seed[:8]}.png" # type: ignore

                profile = user.profile  # type: ignore

                profile.avatar.save(
                    filename,
                    ContentFile(response.content),
                    save=True
                )

                self.stdout.write(
                    self.style.SUCCESS(f"Avatar added for {user.username}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed for {user.username}: {e}")
                )

        self.stdout.write(self.style.SUCCESS("Avatar seeding complete"))