# Generated by Django 4.1.5 on 2023-06-06 13:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_merge_20230605_1724'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='plan_expire',
        ),
        migrations.AlterField(
            model_name='odd',
            name='match',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='payment',
            name='plan',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.plan', verbose_name='Plano'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='type',
            field=models.CharField(choices=[('CARD', 'Cartão'), ('PIX', 'Pix')], editable=False, max_length=100, verbose_name='Tipo'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Cliente'),
        ),
    ]
