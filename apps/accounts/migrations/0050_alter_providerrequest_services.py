# Generated by Django 3.2.18 on 2023-05-08 13:11

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0049_auto_20230507_2146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='providerrequest',
            name='services',
            field=taggit.managers.TaggableManager(blank=True, help_text='Click the services that your organisation offers. These will be listed in the green web directory.', through='accounts.ProviderService', to='accounts.Service', verbose_name='Services offered'),
        ),
    ]
