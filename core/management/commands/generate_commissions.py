from time import sleep
from django.core.management.base import BaseCommand
from core.models import Payment, Commission


class Command(BaseCommand):
    help = 'Generate comissions'

    def handle(self, *args, **options):
        while True:
            for payment in Payment.objects.filter(status=Payment.PaymentStatus.APPROVED, user__referer__isnull=False):
                if Commission.objects.filter(payment=payment).exists():
                    continue

                Commission.objects.create(payment=payment)
                print('Creating commission')

            sleep(20)
