# Generated by Django 4.1.4 on 2022-12-29 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_plan_options_alter_user_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Processed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('surebet_id', models.CharField(max_length=100)),
            ],
        ),
    ]
