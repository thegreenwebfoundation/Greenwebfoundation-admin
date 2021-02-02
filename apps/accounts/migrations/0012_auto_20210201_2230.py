# Generated by Django 2.2.17 on 2021-02-01 22:30

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_auto_20210107_1245'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hostingprovider',
            name='partner',
            field=models.CharField(blank=True, choices=[('', 'None'), ('Partner', 'Partner'), ('Dev Partner', 'Dev Partner'), ('Certified Gold Partner', 'Certified Gold Partner'), ('Certified Partner', 'Certified Partner'), ('Gold Partner', 'Gold Partner')], default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='date_joined',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='date joined'),
        ),
        migrations.AlterField(
            model_name='user',
            name='hostingprovider',
            field=models.ForeignKey(db_column='id_hp', null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.Hostingprovider', unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='legacy_password',
            field=models.CharField(db_column='password', max_length=128, verbose_name='legacy_password'),
        ),
    ]
