# Generated by Django 4.1.5 on 2023-01-21 23:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_plan_cheap_percent_plan_month_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='referer',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Indicado por'),
        ),
    ]