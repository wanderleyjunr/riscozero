# Generated by Django 4.1.5 on 2023-06-05 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_odd_live_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='live_only',
            field=models.BooleanField(default=False, help_text='Marque esta opção caso o plano em questão deva contemplar apenas as apostas do tipo Live', verbose_name='Apenas Live?'),
        ),
    ]