# Generated by Django 3.1.5 on 2021-03-12 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0002_auto_20201116_2152"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalverbalautopsy",
            name="instanceid",
            field=models.TextField(blank=True, verbose_name="Instance ID"),
        ),
        migrations.AddField(
            model_name="verbalautopsy",
            name="instanceid",
            field=models.TextField(blank=True, verbose_name="Instance ID"),
        ),
    ]
