# Generated by Django 3.2.16 on 2023-01-11 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0035_private_public_evidence'),
    ]

    operations = [
        migrations.AddField(
            model_name='providerrequestevidence',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='providerrequestevidence',
            name='type',
            field=models.CharField(choices=[('Annual report', 'Annual Report'), ('Web page', 'Web Page'), ('Certificate', 'Certificate'), ('Other', 'Other')], max_length=255),
        ),
    ]
