from _decimal import Decimal

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from core.models import User, Plan, Payment, Commission

UserAdmin.list_display += ('plan', 'plan_is_active',)  # don't forget the commas
UserAdmin.list_filter += ('plan', 'plan_is_active', 'plan_expire')
UserAdmin.fieldsets += (
        (
            'Planos',
            {
                'fields': (
                    'plan',
                    'plan_is_active',
                    'plan_expire'
                ),
            },
        ),
    )


@admin.register(User)
class UserAdmin(UserAdmin):
    change_form_template = 'loginas/change_form.html'
    list_display = [
        'username',
        'first_name',
        'date_joined',
        'plan_expire',
        'plan',
        'plan_is_active',
        'referer',
        'email',
        'whatsapp',
        
    ]


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'months',
        'amount',
        'month_amount',
        'cheap_percent',
        'commission_percent',
        'created'
    ]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'get_user_email',
        'plan',
        'get_plan_name',
        'type',
        'status',
        'created'
    ]
    ordering = [
        '-created'
    ]
    list_editable = [
        'status'
    ]
    search_fields = [
        'user__username'
    ]

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email do usuário'

    def get_plan_name(self, obj):
        return obj.plan.name if obj.plan else ''
    get_plan_name.short_description = 'Nome do plano'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'plan')
        return queryset

    def save_model(self, request, obj, form, change):
        if obj.status == Payment.PaymentStatus.APPROVED:
            # Atualizar o plano do usuário apenas se o pagamento estiver aprovado
            user = obj.user
            user.plan = obj.plan
            user.plan_is_active = True
            user.save()
            obj.user.set_plan_expiration_date(obj.created, obj.plan.months)

        super().save_model(request, obj, form, change)


@admin.action(description='Marcar comissões como pagas')
def change_status(modeladmin, request, queryset):
    queryset.update(status=Commission.CommissionStatus.PAID, date=timezone.localtime().date())
    messages.success(request, 'Comissões pagas com sucesso!')


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = [
        'get_payment_user',
        'get_payment_referer',
        'get_payment_plan',
        'get_payment_plan_amount',
        'get_payment_plan_commission_percent',
        'get_payment_commission_amount',
        'status',
        'date'
    ]
    search_fields = [
        'payment__user__referer__username'
    ]
    list_filter = [
        'status'
    ]
    actions = [
        change_status
    ]

    @admin.display(description='Usuário', ordering='-payment__plan__user__username')
    def get_payment_user(self, o):
        return o.payment.user.username

    @admin.display(description='Indicado por', ordering='-payment__plan__user_referer__username')
    def get_payment_referer(self, o):
        return o.payment.user.referer.username

    @admin.display(description='Plano', ordering='-payment__plan__name')
    def get_payment_plan(self, o):
        return o.payment.plan.name

    @admin.display(description='Valor do Plano', ordering='-payment__plan__amount')
    def get_payment_plan_amount(self, o):
        return o.payment.plan.amount

    @admin.display(description='% comissão', ordering='-payment__plan__commission_percent')
    def get_payment_plan_commission_percent(self, o):
        return str(round(o.payment.plan.commission_percent, 2)) + '%'

    @admin.display(description='Valor da Comissão')
    def get_payment_commission_amount(self, o):
        return round(o.payment.plan.amount * (Decimal(o.payment.plan.commission_percent / 100)), 2)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
