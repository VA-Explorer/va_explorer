# Generated by Django 3.1.7 on 2021-03-02 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0006_auto_20210128_1119"),
    ]

    operations = [
        migrations.AlterField(
            model_name="causecodingissue",
            name="settings",
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name="causeofdeath",
            name="settings",
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name="historicalcauseofdeath",
            name="settings",
            field=models.JSONField(),
        ),
    ]
