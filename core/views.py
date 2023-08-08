import json
import os
import pickle
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import TemplateView
from core.forms import UserForm
from core.models import Odd, User, HOUSES, Plan, Payment
from core.surebet import cookies

from django.http import HttpResponse
import sys
import time
from datetime import datetime

import mercadopago

from django.db.models import Sum
from django.utils import timezone
from django.db.models import Count
import requests

def cancel_plans(request):
    sys.stdout = open('output.txt', 'a')  # abre o arquivo de saída em modo de escrita
    while True:
        time.sleep(10)
        now = timezone.now()
        for user in User.objects.filter(is_superuser=False, plan_is_active=True, plan_expire__lte=now):
            user.plan_is_active = False
            user.save()
            message = f'{now} - Desativando plano do usuário {user.username}'
            print(message)
    return HttpResponse("Cancel Plans process started")

def atualizar_expiracao_plano(request):
    # Obter todos os pagamentos pagos
    pagamentos_aprovados = Payment.objects.filter(status=Payment.PaymentStatus.APPROVED)

    # Atualizar a data de expiração do plano para cada usuário correspondente
    for pagamento in pagamentos_aprovados:
        pagamento.user.set_plan_expiration_date(pagamento.created, pagamento.plan.months)

    return render(request, 'atualizar_expiracao_plano.html')

def relatorio_view(request):
        total_vendas = Payment.objects.count()
        total_vendas_pagas = Payment.objects.filter(status='APPROVED').count()
        total_vendas_canceladas = Payment.objects.filter(status='EXPIRED').count()
        total_vendas_pendentes = Payment.objects.filter(status='PENDING').count()

        valor_pedidos = Payment.objects.aggregate(Sum('plan__amount'))
        valor_pedidos_pagos = Payment.objects.filter(status='APPROVED').aggregate(Sum('plan__amount'))
        valor_pedidos_cancelados = Payment.objects.filter(status='EXPIRED').aggregate(Sum('plan__amount'))
        valor_pedidos_pendentes = Payment.objects.filter(status='PENDING').aggregate(Sum('plan__amount'))

        clientes_total = User.objects.count()
        clientes_ativos = User.objects.filter(plan_is_active=True).count()
        clientes_inativos = User.objects.filter(plan_is_active=False, plan_id__isnull=False).count()
        clientes_sem_plano = User.objects.filter(plan_is_active=False, plan_id__isnull=True).count()

        clientes_por_plano = User.objects.values('plan__name').annotate(count=Count('plan'),sum_amount=Sum('plan__amount')).order_by('-count')

        context = {
            'total_vendas': total_vendas,
            'total_vendas_pagas': total_vendas_pagas,
            'total_vendas_canceladas': total_vendas_canceladas,
            'total_vendas_pendentes': total_vendas_pendentes,
            'valor_pedidos': valor_pedidos,
            'valor_pedidos_pagos': valor_pedidos_pagos,
            'valor_pedidos_cancelados': valor_pedidos_cancelados,
            'valor_pedidos_pendentes': valor_pedidos_pendentes,
            'clientes_total': clientes_total,
            'clientes_ativos': clientes_ativos,
            'clientes_inativos': clientes_inativos,
            'clientes_sem_plano': clientes_sem_plano,
            'clientes_por_plano': clientes_por_plano,
        }

        return render(request, 'relatorio.html', context)


class PasswordResetView(BasePasswordResetView):
    template_name = 'password_reset_form.html'


class PasswordResetDoneView(TemplateView):
    template_name = 'password_reset_done.html'


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('login')


class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect(reverse_lazy('login'))


@method_decorator([login_required], name='dispatch')
class RefreshView(View):
    def get(self, request):
        refresh_page = request.session.get('refresh_page')

        if refresh_page:
            del request.session['refresh_page']
        else:
            request.session['refresh_page'] = True

        return redirect(request.META['HTTP_REFERER'])


class LoginView(TemplateView):
    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('dashboard'))
        return super().get(request)

    def post(self, request):
        user = User.objects.filter(email=request.POST.get('email')).first()

        if user and user.check_password(request.POST.get('password')):
            login(request, user)
            user.set_session_key(request.session.session_key)
            return redirect(reverse_lazy('dashboard'))

        messages.error(request, 'Usuário ou senha incorretos')
        return redirect(reverse_lazy('login'))


@method_decorator(user_passes_test(lambda u: u.is_anonymous), name='dispatch')
class RegisterView(TemplateView):
    template_name = 'register.html'

    def post(self, request):
        form = UserForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form
            })

        referer = None

        if 'referer' in request.session:
            referer = User.objects.get(email=request.session['referer'])

        user = User.objects.create(
            first_name=form.cleaned_data['name'],
            email=form.cleaned_data['email'],
            whatsapp=form.cleaned_data['whatsapp'],
            username=form.cleaned_data['email'],
            is_active=True,
            referer=referer
        )
        user.set_password(form.cleaned_data['password'])
        user.save()

        login(request, user)
        user.set_session_key(request.session.session_key)
        return redirect(reverse_lazy('dashboard'))


@method_decorator([login_required], name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        live_houses = 'DafaSports,Vbet,leovegas,Betano,Pinnacle,PariMatch,Netbet,KTO,Sportingbet,Bodog,Betway,Betsson,bet365,888sport,188bet,Betfair,Novibet'.split(',')
        context = super().get_context_data(**kwargs)
        context['houses'] = HOUSES
        context['user_houses'] = self.request.user.houses.split(',')
        context['sports'] = Odd.objects.values_list('sport', flat=True).distinct()
        context['live_houses'] = [c.lower() for c in live_houses]

        if not self.request.user.sports:
            user = self.request.user
            user.sports = ','.join(context['sports'])
            user.save()

        context['user_sports'] = self.request.user.sports.split(',')
        context['plans'] = Plan.objects.all()
        return context

    def post(self, request):
        order_choices = [
            'minutes',
            'date',
            'profit'
        ]

        time = request.POST.get('time')
        order = request.POST.get('order')
        profit_start = Decimal(request.POST.get('profit_start', '0') or '0')
        profit_end = Decimal(request.POST.get('profit_end', '0') or '0')

        if profit_end <= 0:
            profit_end = 1000

        houses = request.POST.getlist('houses[]')
        sports = request.POST.getlist('sports[]')
        houses_sanitized = []
        user = request.user

        if order in order_choices:
            user.order = '-' + order

        for house in houses:
            if house in HOUSES:
                houses_sanitized.append(house)

        if request.user.is_authenticated:
            user.profit_start = profit_start
            user.profit_end = profit_end
            user.time = time
            user.houses = ','.join(houses)
            user.sports = ','.join(sports)
            user.save()

        return redirect(request.META['HTTP_REFERER'])


@method_decorator([login_required, xframe_options_exempt], name='dispatch')
class OddsView(TemplateView):
    template_name = 'odds.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        order_by = [user.order]
        limit = 0

        if not user.plan_is_active:
            order_by = ['profit']
            limit = 20

        if 'date' in user.order:
            order_by = ['date', 'hour']

        houses_diff = [h for h in HOUSES if h not in user.houses.split(',')]

        removed_odds_session = self.request.session.get('removed_odds')
        removed_odds = removed_odds_session.split(',') if removed_odds_session else []
        order_by.append('house')

        if not user.time:
            user.time = 'a'
            user.save()

        profit_end = user.profit_end

        if not user.plan_is_active:
            profit_end = 1

        surebet_items = Odd.objects.filter(
            profit__gte=user.profit_start,
            profit__lte=profit_end,
            house__in=user.houses.split(','),
            sport__in=user.sports.split(','),
            is_live=False
        )

        filter_time = None

        if user.time.endswith('h'):
            filter_time = timezone.localtime() + timedelta(hours=int(user.time.strip('h')))
        elif user.time.endswith('w'):
            filter_time = timezone.localtime() + timedelta(weeks=int(user.time.strip('w')))

        if filter_time:
            surebet_items = surebet_items.filter(timestamp__lte=filter_time)

        surebet_items = surebet_items.exclude(
            house__in=houses_diff
        ).order_by(
            *order_by
        )

        surebet_qs = {}

        for surebet_item in surebet_items:
            if surebet_item.surebet_id in removed_odds:
                continue

            if surebet_item.surebet_id not in surebet_qs.keys():
                surebet_qs[surebet_item.surebet_id] = [surebet_item]
            elif surebet_qs[surebet_item.surebet_id][0].house != surebet_item.house:
                surebet_qs[surebet_item.surebet_id].append(surebet_item)

        surebet_qs = {surebet_id: odds for surebet_id, odds in surebet_qs.items() if len(odds) == 2}

        context['houses'] = HOUSES
        context['user_houses'] = user.houses.split(',')
        context['odds'] = surebet_qs
        context['qty'] = len(surebet_qs.keys()) if limit == 0 else limit
        context['limit'] = limit
        return context


@method_decorator(csrf_exempt, name='dispatch')
class KiwifyView(View):
    def post(self, request):
        body_unicode = request.body.decode('utf-8')

        with transaction.atomic():
            body = json.loads(body_unicode)
            user, created = User.objects.get_or_create(email=body['Customer']['email'])

            if body['order_status'] == 'paid':
                user.plan_is_active = True
                user.plan = Plan.objects.first()

            if created:
                user.first_name = body['Customer']['full_name'].split(' ', 1)[0]
                user.last_name = body['Customer']['full_name'].split(' ', 1)[1]
                user.is_active = True
                user.set_password(body['Customer']['full_name'].split(' ', 1)[0].lower().strip() + '123')
                user.save()

            return HttpResponse('', status=201)


@method_decorator([login_required, xframe_options_exempt], name='dispatch')
class LiveView(TemplateView):
    template_name = 'live.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        odds = {}
        user = self.request.user

        profit_end = user.profit_end

        if not user.plan_is_active:
            profit_end = 1

        surebet_qs = Odd.objects.filter(
            profit__gte=user.profit_start,
            profit__lte=profit_end,
            house__iregex='|'.join([c.lower() for c in user.houses.split(',')]),
            is_live=True
        )

        for odd in surebet_qs:
            if odd.surebet_id in odds and len(odds[odd.surebet_id]) >= 2:
                continue
            elif odd.surebet_id not in odds:
                odds[odd.surebet_id] = [odd]
            else:
                odds[odd.surebet_id].append(odd)

        keys = list(odds.keys())

        for key in keys:
            if len(odds[key]) < 2:
                del odds[key]

        context['odds'] = odds
        context['qty'] = len(odds.keys())
        return context


class RedirectView(View):
    def get(self, request, surebet_id, house):
        odd = Odd.objects.filter(surebet_id=surebet_id, house__iexact=house).first()

        if not odd:
            return redirect(reverse_lazy('login'))

        options = Options()
        options.page_load_strategy = 'eager'
        options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        options.add_argument('--no-sandbox')
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options, seleniumwire_options={'request_storage': 'memory'})

        if odd.is_live:
            driver.get('https://www.betburger.com/br/arbs/live')
            if os.path.exists('cookies.pkl'):
                for cookie in pickle.load(open("cookies.pkl", "rb")):
                    driver.add_cookie(cookie)
        else:
            driver.get('https://pt.surebet.com/surebets')

            for name, value in cookies.items():
                driver.add_cookie({
                    'name': name,
                    'value': value,
                    'domain': '.surebet.com'
                })

        driver.get(odd.anchor)
        redirect_uri = driver.current_url.replace('https://pari-match.com/', 'https://br.parimatch.com/')

        if 'betano' in odd.house.lower():
            for request in driver.requests:
                if 'br.betano.com/' in request.url and 'myaccount/ban' not in request.url:
                    redirect_uri = request.url
                    break
        elif '188bet' in odd.house.lower():
            for request in driver.requests:
                if '188bet.com/' in request.url and '/forbidden' not in request.url:
                    redirect_uri = request.url
                    break
        elif 'vbet' in odd.house.lower():
            for request in driver.requests:
                if 'www.vbet.com/' in request.url and 'eventId' in request.url:
                    redirect_uri = request.url
                    break
        elif 'betmotion.com' in odd.house.lower():
            for request in driver.requests:
                if 'betmotion.com/' in request.url:
                    redirect_uri = request.url
                    break

        if 'surebet.com' not in driver.current_url:
            r = redirect(redirect_uri)
            return r

        driver.quit()
        Odd.objects.filter(surebet_id=odd.surebet_id, is_live=False).delete()
        return redirect(reverse_lazy('login'))


class CalcView(TemplateView):
    template_name = 'calc.html'

    def get(self, request, surebet_id, house1, house2):
        context = self.get_context_data()
        odds = Odd.objects.filter(surebet_id=surebet_id, house__in=[house1, house2])
        odds_cache = []

        for odd in odds:
            if not odds_cache:
                odds_cache.append(odd)
            elif odds_cache[0].house != odd.house:
                odds_cache.append(odd)
                break

        odds = odds_cache

        context['odds'] = odds
        return render(request, self.template_name, context)


@method_decorator([login_required], name='dispatch')
class RemoveView(View):
    def get(self, request, surebet_id):
        removed_odds = request.session.get('removed_odds', '').split(',')
        if surebet_id not in removed_odds:
            removed_odds.append(surebet_id)
        request.session['removed_odds'] = ','.join(removed_odds)
        return redirect(reverse_lazy('odds'))


@method_decorator([login_required, csrf_exempt], name='dispatch')
class ProcessPayment(View):
    def post(self, request):
        plan_id = request.POST['plan_id']
        plan = Plan.objects.get(id=plan_id)

        sdk = mercadopago.SDK('APP_USR-1148758092661391-022511-d9c709a052ed273e787b18f0e2435b7d-55690751')

        payment_data = {
            "transaction_amount": float(round(plan.amount, 2)),
            "description": plan.name,
            "payment_method_id": "pix",
            "notification_url": 'https://sinais.sempregreen.com.br' + reverse_lazy('notification'),
            "payer": {
                "email": request.POST['email'],
                "first_name": request.POST['payerFirstName'],
                "last_name": request.POST['payerLastName'],
                "identification": {
                    "type": request.POST['identificationType'],
                    "number": request.POST['identificationNumber']
                }
            }
        }

        payment_response = sdk.payment().create(payment_data)
        identifier = payment_response["response"]["id"]
        pagamento = Payment.objects.create(
            identifier=str(identifier),
            response=json.dumps(payment_response),
            type=Payment.PaymentType.PIX,
            user=request.user,
            plan=plan
        )

        user = User.objects.get(id=request.user.id)
        user.set_plan_expiration_date(pagamento.created, pagamento.plan.months)
        user.save()

        return redirect(payment_response["response"]['point_of_interaction']['transaction_data']['ticket_url'])


@method_decorator([login_required, csrf_exempt], name='dispatch')
class ProcessPaymentCard(View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        plan_id = data.get('plan_id')
        plan = Plan.objects.get(id=plan_id)

        notification_uri = 'https://apostariscozero.com' + reverse_lazy('notification')
        sdk = mercadopago.SDK('APP_USR-1148758092661391-022511-d9c709a052ed273e787b18f0e2435b7d-55690751')

        payment_data = {
            "transaction_amount": float(data.get("transaction_amount")),
            "token": data.get("token"),
            "description": plan.name,
            "installments": int(data.get("installments")),
            "payment_method_id": data.get("payment_method_id"),
            "notification_url": notification_uri,
            "payer": {
                "email": data["payer"]["email"],
                "identification": {
                    "type": data["payer"]["identification"]["type"],
                    "number": data["payer"]["identification"]["number"]
                }
            }
        }
        payment_response = sdk.payment().create(payment_data)

        try:
            identifier = payment_response["response"]["id"]
        except KeyError:
            return HttpResponse('', status=403)

        status = payment_response["response"]['status'].lower()

        if status != 'approved':
            return HttpResponse('', status=403)

        pagamento = Payment.objects.create(
            identifier=str(identifier),
            response=json.dumps(payment_response),
            type=Payment.PaymentType.CARD,
            user=request.user,
            plan=plan,
            status=Payment.PaymentStatus.APPROVED
        )

        if status == 'approved':
            user = User.objects.get(id=request.user.id)
            user.plan = plan
            user.plan_is_active = True
            user.set_plan_expiration_date(pagamento.created, pagamento.plan.months)
            user.save()

        return HttpResponse('', status=201)


@method_decorator([login_required], name='dispatch')
class IndicationsView(TemplateView):
    template_name = 'indications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['indications'] = User.objects.filter(referer=self.request.user).order_by('-date_joined')
        return context


class RefererView(View):
    def get(self, request, email):
        try:
            User.objects.get(email=email)
            request.session['referer'] = email
        except User.DoesNotExist:
            ...

        return redirect(reverse_lazy('register'))


@method_decorator(csrf_exempt, name='dispatch')
class PaymentNotification(View):
    def post(self, request):
        data = json.loads(request.body.decode())
        payment = Payment.objects.get(identifier=str(data['data']['id']))
        token = 'APP_USR-1148758092661391-022511-d9c709a052ed273e787b18f0e2435b7d-55690751'
        url = 'https://api.mercadopago.com/v1/payments/'
        headers = {
            "Authorization": "Bearer " + token
        }

        response = requests.get(url + data['data']['id'], headers=headers)
        dados = response.json()
        mensagem = dados['status'] + ' ' + data['data']['id']

        if data['action'] == 'payment.updated':
            payment.webhook_data = data
            if dados['status'] == 'approved':
                payment.status = Payment.PaymentStatus.APPROVED

                payment.save()

                payment.user.plan = payment.plan
                payment.user.plan_is_active = True
                payment.user.set_plan_expiration_date(payment.modified, payment.plan.months)
                payment.user.save()

        resposta = HttpResponse(status=200)
        resposta.content = mensagem.encode('utf-8')
        return resposta
