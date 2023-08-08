from decimal import Decimal
from importlib import import_module

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from model_utils.models import UUIDModel, TimeStampedModel

HOUSES = [
    '188Bet',
    '22Bet',
    #'20Bet',
    '888sport',
    '1Win',
    '1xBet',
    'AmuletoBet',
    'Bet365',
    'Betano',
    #'Betboo',
    'Betcris',
    'BetFair',
    'Betfair SB',
    # 'Betmotion',
    #'Betfinal',
    'Betnacional',
    'Betsson',
    'Betsul',
    'BetVictor',
    'BetWay',
    'BetWarrior',
    'Blaze',
    #'Bodog',
    # 'Bwin',
    # 'CampoBet',
    'Dafabet',
    'DafaSports',
    'GGBet',
    'GaleraBet',
    'LeoVegas',
    'Marjosports',
    'MrJack',
    'Netbet',
    'NoviBet',
    'Parimatch',
    'KTO',
    'Pin-up',
    'Pinnacle',
    'PixBet',
    'Playpix',
    # 'Pokerstars',
    'Rivalo',
    # 'Sbobet',
    'SportsBet',
    'Sportingbet',
    'Stake',
    'TempoBet',
    # 'TonyBet',
    'VBet',
    'Vulkan Bet',
    'Winmasters'
]


class Base(UUIDModel, TimeStampedModel):
    class Meta:
        abstract = True


class Plan(Base):
    name = models.CharField(max_length=100)
    months = models.IntegerField(default=1, verbose_name='Meses (carência)')
    amount = models.DecimalField(default=1, max_digits=10, decimal_places=2, verbose_name='Valor')
    month_amount = models.DecimalField(default=1, max_digits=10, decimal_places=2, verbose_name='O mês sai por')
    cheap_percent = models.IntegerField(default=1, verbose_name='Você economiza')
    commission_percent = models.IntegerField(default=1, verbose_name='Porcentagem de comissão')
    has_live = models.BooleanField(default=False, verbose_name='Possui Live?', help_text='Marque esta opção caso o plano em questão possua o tipo Live de apostas')
    live_only = models.BooleanField(default=False, verbose_name='Apenas Live?', help_text='Marque esta opção caso o plano em questão deva contemplar apenas as apostas do tipo Live')

    @property
    def mp_amount(self):
        return str(float(round(self.amount, 2)))

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        return self.name


class User(UUIDModel, AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    email = models.EmailField(unique=True)
    order = models.CharField(max_length=100, null=True)
    time = models.CharField(max_length=100, default='a', null=True)
    profit_start = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    profit_end = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    houses = models.TextField(null=True, blank=True)
    sports = models.TextField(null=True, blank=True)
    plan = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='Plano')
    plan_is_active = models.BooleanField(default=False, verbose_name='Plano está ativo?')
    whatsapp = models.CharField(max_length=20, null=True, blank=True, editable=False, verbose_name='WhatsApp')
    referer = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name='Indicado por')
    last_session_key = models.CharField(blank=True, null=True, max_length=40)
    plan_expire = models.DateTimeField(null=True, blank=True, verbose_name='Data de expiração do plano')

    def set_session_key(self, key):
        try:
            if self.last_session_key and not self.last_session_key == key:
                s = import_module(settings.SESSION_ENGINE).SessionStore(session_key=self.last_session_key)
                s.delete()
            self.last_session_key = key
            self.save()
        except:
            ...

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.order = '-profit'
            self.profit_start = Decimal(0)
            self.profit_end = Decimal(1000)
            self.houses = ','.join(HOUSES)
        super().save(*args, **kwargs)

    @property
    def days_expire_plan(self):
        payment = Payment.objects.filter(user=self, status=Payment.PaymentStatus.APPROVED).order_by('-created').first()
        if not payment:
            return 0
        now_date = timezone.localtime().date()
        return ((payment.created + relativedelta(months=payment.plan.months)).date() - now_date).days
    
    def set_plan_expiration_date(self, payment_created, plan):
        # Adicione a lógica para definir a data de expiração do plano com base na data de criação do pagamento
        # Exemplo: definir a data de expiração do plano como 30 dias após a data de criação do pagamento

        self.plan_expire = payment_created + relativedelta(months=plan)
        self.save()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class Odd(Base):
    sport = models.CharField(max_length=255)
    match = models.CharField(max_length=1000)
    date = models.DateField()
    hour = models.TimeField()
    timestamp = models.DateTimeField(null=True)
    minutes = models.IntegerField()
    house = models.CharField(max_length=1000)
    tournament = models.CharField(max_length=1000)
    market = models.TextField()
    profit = models.DecimalField(max_digits=20, decimal_places=8)
    chance = models.DecimalField(max_digits=20, decimal_places=8)
    surebet_id = models.CharField(max_length=1000)
    anchor = models.URLField(null=True, max_length=5000)
    is_live = models.BooleanField(default=False)
    live_color = models.CharField(max_length=1000, null=True)


class Processed(models.Model):
    surebet_id = models.CharField(max_length=100)


class Payment(Base):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        APPROVED = 'APPROVED', 'Aprovado'
        EXPIRED = 'EXPIRED', 'Expirado'

    class PaymentType(models.TextChoices):
        CARD = 'CARD', 'Cartão'
        PIX = 'PIX', 'Pix'

    identifier = models.CharField(max_length=255, editable=False, verbose_name='Identificador Único')
    response = models.TextField(editable=False, verbose_name='Resposta')
    webhook_data = models.TextField(null=True, editable=False, verbose_name='Dados do Webhook')
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=True, verbose_name='Cliente')
    plan = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, editable=True, verbose_name='Plano')
    status = models.CharField(max_length=100, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name='Status')
    type = models.CharField(editable=True, max_length=100, choices=PaymentType.choices, verbose_name='Tipo')

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'


class Commission(Base):
    class CommissionStatus(models.TextChoices):
        WAITING = 'WAITING', 'Pendente de Pagamento'
        PAID = 'PAID', 'Pago'

    status = models.CharField(editable=False, max_length=100, choices=CommissionStatus.choices, default=CommissionStatus.WAITING, verbose_name='Status')
    date = models.DateField(null=True, editable=False, verbose_name='Data de pagamento da comissão')
    payment = models.ForeignKey(Payment, null=True, on_delete=models.CASCADE, editable=False, verbose_name='Pagamento')

    class Meta:
        verbose_name = 'Comissão'
        verbose_name_plural = 'Comissões'
