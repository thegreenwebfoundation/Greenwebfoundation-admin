# Generated by Django 3.2.16 on 2023-01-18 17:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0038_provider_request_consent"),
    ]

    operations = [
        migrations.AddField(
            model_name="hostingprovider",
            name="city",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
