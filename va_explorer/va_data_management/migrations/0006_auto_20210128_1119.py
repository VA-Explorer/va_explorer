# Generated by Django 3.0.8 on 2021-01-28 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0005_cod_codes_dhis"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dhisstatus",
            name="status",
            field=models.TextField(default="SUCCESS"),
        ),
    ]
