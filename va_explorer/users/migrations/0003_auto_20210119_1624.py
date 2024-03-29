# Generated by Django 3.0.8 on 2021-01-19 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("va_data_management", "0002_auto_20201116_2152"),
        ("users", "0002_auto_20201002_2331"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="locations",
        ),
        migrations.AddField(
            model_name="user",
            name="location_restrictions",
            field=models.ManyToManyField(
                db_table="users_user_location_restrictions",
                related_name="users",
                to="va_data_management.Location",
            ),
        ),
    ]
