# Generated by Django 4.1.2 on 2023-02-22 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('va_data_management', '0020_remove_historicalverbalautopsy_username_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalverbalautopsy',
            name='username',
            field=models.TextField(blank=True, verbose_name='Username'),
        ),
        migrations.AddField(
            model_name='verbalautopsy',
            name='username',
            field=models.TextField(blank=True, verbose_name='Username'),
        ),
    ]
