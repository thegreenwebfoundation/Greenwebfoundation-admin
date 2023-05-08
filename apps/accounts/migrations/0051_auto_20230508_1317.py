# Generated by Django 3.2.18 on 2023-05-08 13:17

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0050_alter_providerrequest_services'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProviderRequestService',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.providerrequest')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts_providerrequestservice_items', to='accounts.service')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='providerrequest',
            name='services',
            field=taggit.managers.TaggableManager(blank=True, help_text='Click the services that your organisation offers. These will be listed in the green web directory.', through='accounts.ProviderRequestService', to='accounts.Service', verbose_name='Services offered'),
        ),
    ]
