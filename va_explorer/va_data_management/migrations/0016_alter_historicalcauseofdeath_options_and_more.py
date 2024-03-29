# Generated by Django 4.0.8 on 2022-10-17 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0015_auto_20220330_1128"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historicalcauseofdeath",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical cause of death",
                "verbose_name_plural": "historical cause of deaths",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalverbalautopsy",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical verbal autopsy",
                "verbose_name_plural": "historical verbal autopsys",
            },
        ),
        migrations.AlterField(
            model_name="historicalcauseofdeath",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalverbalautopsy",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
    ]
