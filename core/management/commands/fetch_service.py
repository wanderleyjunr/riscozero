from time import sleep
from decimal import Decimal
from django.core.management.base import BaseCommand
from django_rq import get_queue
from core.fetch import scraper
from core.models import Processed, Odd


class Command(BaseCommand):
    help = 'Fetch service for pt.surebet.com'

    def handle(self, *args, **options):
        while True:
            odds_queue = get_queue('odds')

            if odds_queue.count == 0:
                ids = []

                for processed in Processed.objects.all():
                    ids.append(processed.surebet_id)

                Odd.objects.filter(profit__lte=Decimal('0.1')).delete()
                Odd.objects.exclude(surebet_id__in=ids).delete()
                Processed.objects.all().delete()

                scraper.delay('/surebets')
                print('Sending for processing...')

            sleep(20)
