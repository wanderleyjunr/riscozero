from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import MultipleChoiceField
from model_utils.models import UUIDModel, TimeStampedModel

from core.models import HOUSES

HOUSES_CHOICES = [(h, h) for h in HOUSES]


class _MultipleChoiceField(MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.pop("base_field", None)
        kwargs.pop("max_length", None)
        super().__init__(*args, **kwargs)


class ChoiceArrayField(ArrayField):
    def formfield(self, **kwargs):
        return super().formfield(**{"form_class": _MultipleChoiceField,
                                    "choices": self.base_field.choices,
                                    **kwargs})


DEFAULT_MESSAGE = """➡️NOVA OPORTUNIDADE 

🏆 ESPORTE: {esporte}
🏳️LIGA: {liga}
🎪EVENTO: {evento}
⏰HORARIO: {horario}
📊LUCRO: {lucro}
📁MERCADO: {mercado}

🏠1° {casa1}
MERCADO: {mercado_casa1}
ODD: {odd_casa1}
Link : {link_casa1}

🏠2° {casa2}
MERCADO: {mercado_casa2}
ODD: {odd_casa2}
Link: {link_casa2}

CALCULADORA: {link_calculadora}

✅VERIFIQUE O VALOR MÁXIMO QUE AS CASAS DEIXAM APOSTAR
✅VERIFIQUE SE AS ODDS NÃO MUDARAM
✅RECOMENDADO: R$ 1000
✅NÃO USAR VALORES QUEBRADOS NAS ENTRADAS"""

class Config(UUIDModel, TimeStampedModel):
    houses = ChoiceArrayField(
        models.CharField(max_length=100, choices=HOUSES_CHOICES, verbose_name='Casas')
    )
    min_profit = models.DecimalField(decimal_places=2, max_digits=20, verbose_name='Lucro mínimo')
    max_profit = models.DecimalField(decimal_places=2, max_digits=20, verbose_name='Lucro máximo')
    message = models.TextField(default=DEFAULT_MESSAGE, verbose_name='Mensagem')
    min_chance = models.DecimalField(null=True, decimal_places=2, max_digits=20, verbose_name='Odd mínima')
    max_chance = models.DecimalField(null=True, decimal_places=2, max_digits=20, verbose_name='Odd máxima')
    minutes = models.IntegerField(default=1, verbose_name='Minutos', help_text='Enviar a cada x minutos')
    bot_token = models.CharField(null=True, max_length=255, verbose_name='Bot Token')
    chat_id = models.BigIntegerField(null=True, verbose_name='Chat ID')
    sent_timestamp = models.DateTimeField(null=True, editable=False)
    per_time = models.IntegerField(default=1, verbose_name='Qtd. Sinais', help_text='Quantidade de sinais a serem enviados a cada x minutos')

    def __str__(self):
        return f'{",".join(self.houses)} {self.minutes} minutos'

    class Meta:
        verbose_name = 'Telegram - Configuração'
        verbose_name_plural = 'Telegram - Configurações'


class Sent(UUIDModel, TimeStampedModel):
    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    surebet_id = models.CharField(max_length=100)
