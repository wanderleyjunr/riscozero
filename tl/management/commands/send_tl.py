import asyncio
import time

from decimal import Decimal
from django.core.management import BaseCommand
from django.utils import timezone
from telegram import Bot
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from core.models import Odd
from tl.models import Config, Sent


async def send_message(bot_token, content, chat_id):
    bot = Bot(bot_token)
    await bot.send_message(text=content,
                           chat_id=chat_id,
                           parse_mode=ParseMode.MARKDOWN_V2,
                           disable_web_page_preview=True)


class Command(BaseCommand):
    help = ''

    def handle(self, *args, **options):
        while True:
            for conf in Config.objects.all():
                if conf.sent_timestamp and (
                        (timezone.localtime() - conf.sent_timestamp).total_seconds() / 60) < conf.minutes:
                    continue

                houses = [h for h in conf.houses]
                qs = Odd.objects.filter(house__in=houses,
                                        profit__gte=conf.min_profit,
                                        profit__lte=conf.max_profit,
                                        chance__gte=conf.min_chance,
                                        chance__lte=conf.max_chance)

                odds = {}

                for odd in qs:
                    if odd.house not in houses:
                        continue

                    if odd.house in ['Bet365', 'Pinnacle'] and odd.chance > Decimal(1.60):
                        continue

                    if odd.surebet_id not in odds:
                        odds[odd.surebet_id] = [odd]
                    elif odds[odd.surebet_id][0].house != odd.house:
                        odds[odd.surebet_id].append(odd)

                exclude = []

                for key, value in odds.items():
                    if len(odds[key]) != 2:
                        exclude.append(key)

                odds = {key: odd for key, odd in odds.items() if key not in exclude}

                if len(odds.keys()) == 0:
                    continue

                index = 1

                for key, odds in odds.items():
                    if Sent.objects.filter(surebet_id=key, config=conf).exists():
                        continue

                    message_map = {
                        'esporte': escape_markdown(odds[0].sport, 2),
                        'liga': escape_markdown(odds[0].tournament, 2),
                        'evento': escape_markdown(odds[0].match, 2),
                        'horario': escape_markdown(f'{odds[0].date} {odds[0].hour}', 2),
                        'lucro': escape_markdown(f'{round(odds[0].profit, 2)}%', 2),
                        'mercado': escape_markdown(odds[0].market.split('title="', 1)[1].split('"', 1)[0].strip(), 2),
                        'casa1': escape_markdown(odds[0].house, 2),
                        'mercado_casa1': escape_markdown(odds[0].market.split('title="', 1)[1].split('"', 1)[0].strip(),
                                                         2),
                        'odd_casa1': escape_markdown(str(round(odds[0].chance, 2)), 2),
                        'link_casa1': escape_markdown(
                            f'https://apostariscozero.com/redirect/{odds[0].surebet_id}/{odds[0].house}', 2),
                        'mercado_casa2': escape_markdown(odds[1].market.split('title="', 1)[1].split('"', 1)[0].strip(),
                                                         2),
                        'casa2': escape_markdown(odds[1].house, 2),
                        'odd_casa2': escape_markdown(str(round(odds[1].chance, 2)), 2),
                        'link_casa2': escape_markdown(
                            f'https://apostariscozero.com/redirect/{odds[1].surebet_id}/{odds[1].house}', 2),
                        'link_calculadora': escape_markdown(
                            f'https://apostariscozero.com/calc/{odds[1].surebet_id}/{odds[0].house}/{odds[1].house}',
                            2),
                    }

                    asyncio.run(send_message(
                        conf.bot_token,
                        conf.message.format(**message_map),
                        conf.chat_id
                    ))

                    Sent.objects.create(config=conf, surebet_id=key)

                    if index == conf.per_time:
                        break

                    index += 1

                conf.sent_timestamp = timezone.localtime()
                conf.save()

            time.sleep(1)
