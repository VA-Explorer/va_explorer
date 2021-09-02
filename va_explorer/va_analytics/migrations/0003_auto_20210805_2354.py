# Generated by Django 3.1.5 on 2021-08-05 23:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('va_analytics', '0002_update_dashboard_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dashboard',
            options={'default_permissions': ('view',), 'managed': False, 'permissions': (('download_data', 'Can download data'), ('view_pii', 'Can view PII in data'), ('supervise_users', 'Can supervise other users'))},
        ),
    ]
