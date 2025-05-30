# Generated by Django 5.1.4 on 2025-04-02 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Family', '0010_remove_familysettings_finance_notifications_and_more'), ]

    operations = [
        migrations.AlterField(
            model_name='familysettings',
            name='task_notifications',
            field=models.CharField(
                choices=[
                    ('all',
                     'Visi šeimos nariai'),
                    ('parents',
                     'Tik tėvai'),
                    ('admin',
                     'Tik administratorius')],
                default='all',
                max_length=20,
                verbose_name='Užduočių pranešimai'),
        ),
    ]
