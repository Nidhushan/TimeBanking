# Generated by Django 5.1.1 on 2024-12-04 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Time_Banking", "0006_notification_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="url",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]