from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Generate a new random Django SECRET_KEY for use in .env"

    def handle(self, *args, **options):
        self.stdout.write(get_random_secret_key())
