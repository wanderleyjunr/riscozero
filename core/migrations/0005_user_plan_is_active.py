# Generated by Django 4.1.4 on 2022-12-26 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_plan_user_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='plan_is_active',
            field=models.BooleanField(default=False, verbose_name='Plano está ativo?'),
        ),
    ]
