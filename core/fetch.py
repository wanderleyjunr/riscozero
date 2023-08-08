import datetime
from decimal import Decimal

import requests
from django.utils import timezone
from django.utils.timezone import make_aware

from django_rq import job
from selectolax.parser import HTMLParser

from core.models import Odd, Processed
from core.surebet import cookies, headers, BASE_URL


@job('odds')
def scraper(endpoint):
    r = requests.get(BASE_URL + endpoint, cookies=cookies, headers=headers, timeout=5)

    parser = HTMLParser(r.text)
    surebet_records = parser.css('.surebet_record')
    now_time = timezone.localtime()

    for surebet_record in surebet_records:
        surebet_rows = surebet_record.css('tr:not(:last-child)')
        profit = Decimal('0.00')
        minutes = 0

        for surebet_row in surebet_rows:
            profit_element = surebet_row.css_first('.profit-box .profit')

            if profit_element:
                profit = Decimal(profit_element.text().strip('%').replace(',', '.'))

            age_element = surebet_row.css_first('.profit-box .age')

            if age_element:
                age = age_element.text().strip().split()

                if age[1].startswith('m'):
                    minutes = int(age[0])
                if age[1].startswith('h'):
                    minutes = int(age[0]) * 60

            match_datetime = datetime.datetime.strptime(surebet_row.css_first('.time').text(), '%d/%m%H:%M')
            year = now_time.year

            if match_datetime.month < now_time.month:
                year = now_time.year + 1

            match_datetime = match_datetime.replace(year=year)
            house_name = surebet_row.css_first('.booker a').text().encode('ascii', 'ignore').decode().replace('(BR)', '').strip()
            match = surebet_row.css_first('.event a').text()
            tournament = surebet_row.css_first('.event > span.minor').text()
            surebet_id = surebet_row.css_first('.event a').attributes['href'].split('/')[-2]
            market = surebet_row.css_first('.coeff abbr').html
            chance = Decimal(surebet_row.css_first('.value').text().strip().split()[0])
            anchor = BASE_URL + surebet_row.css_first('.event a').attributes['href']
            sport = surebet_row.css_first('.booker > .minor').text().strip()

            if house_name.startswith('Dafabet'):
                house_name = 'Dafabet'
            if house_name.startswith('Bodog'):
                house_name = 'Bodog'
            if house_name.startswith('Bwin'):
                house_name = 'Bwin'
            if house_name.startswith('Betfair SB'):
                house_name = 'Betfair SB'
            if house_name.startswith('Sportingbet'):
                house_name = 'Sportingbet'

            print('Fetching odd', match, surebet_id, chance)

            odd_qs = Odd.objects.filter(
                surebet_id=surebet_id,
                house=house_name,
                match=match,
                market=market
            )

            kwargs = dict(
                profit=profit,
                minutes=minutes,
                date=match_datetime.date(),
                hour=match_datetime.time(),
                timestamp=make_aware(match_datetime),
                house=house_name,
                match=match,
                sport=sport,
                tournament=tournament,
                market=market,
                surebet_id=surebet_id,
                chance=chance,
                anchor=anchor
            )

            if not Processed.objects.filter(surebet_id=surebet_id).exists():
                Processed.objects.create(surebet_id=surebet_id)

            if odd_qs.exists():
                odd_qs.update(**kwargs)
            else:
                Odd.objects.create(**kwargs)

    endpoints = []

    if 'like=' not in endpoint:
        for a in parser.css('a[href*="surebets/group"]'):
            if '//' not in a.attributes['href']:
                endpoints.append(a.attributes['href'])

    next_page = parser.css_first('a.next_page')

    if next_page and 'disabled' not in next_page.attributes['class']:
        endpoints.append(next_page.attributes['href'])

    for endpoint in endpoints:
        scraper.delay(endpoint)
