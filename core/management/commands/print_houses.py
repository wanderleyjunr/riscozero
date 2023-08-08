from django.core.management.base import BaseCommand

from core.models import Odd


class Command(BaseCommand):
    help = 'Generate comissions'

    def handle(self, *args, **options):
        houses = []

        for odd in Odd.objects.all():
            if odd.house not in houses:
                houses.append(odd.house)

        for house in houses:
            print(house)
