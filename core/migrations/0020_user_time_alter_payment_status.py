# Generated by Django 4.1.5 on 2023-02-04 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_alter_payment_plan_alter_payment_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='time',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pendente'), ('APPROVED', 'Aprovado'), ('EXPIRED', 'Expirado')], default='PENDING', max_length=100, verbose_name='Status'),
        ),
    ]
