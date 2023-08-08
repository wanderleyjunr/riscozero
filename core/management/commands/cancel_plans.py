import sys
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Generate comissions'

    def handle(self, *args, **options):
        sys.stdout = open('output.txt', 'a')  # abre o arquivo de saída em modo de escrita
        while True:
            time.sleep(10)
            for user in User.objects.filter(is_superuser=False):
                if user.days_expire_plan <= 0 and user.plan_is_active:
                    user.plan_is_active = False
                    user.save()
                    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    message = f'{now} - Desativando plano do usuário {user.username}'
                    print(message)