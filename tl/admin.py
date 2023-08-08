from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from tl.models import Config, ChoiceArrayField


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    formfield_overrides = {
        ChoiceArrayField: {'widget': CheckboxSelectMultiple}
    }
    list_display = [
        'houses',
        'message',
        'min_profit',
        'max_profit',
    ]
