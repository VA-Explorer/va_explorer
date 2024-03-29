# Generated by Django 3.0.8 on 2021-01-25 05:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0003_dhisstatus"),
    ]

    operations = [
        migrations.AddField(
            model_name="dhisstatus",
            name="verbalautopsy",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dhisva",
                to="va_data_management.VerbalAutopsy",
            ),
            preserve_default=False,
        ),
    ]
