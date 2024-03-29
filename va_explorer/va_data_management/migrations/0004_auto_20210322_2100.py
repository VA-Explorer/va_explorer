# Generated by Django 3.1.5 on 2021-03-22 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0003_auto_20210312_1905"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalverbalautopsy",
            name="submissiondate",
            field=models.TextField(blank=True, verbose_name="Submission Date"),
        ),
        migrations.AddField(
            model_name="verbalautopsy",
            name="submissiondate",
            field=models.TextField(blank=True, verbose_name="Submission Date"),
        ),
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
