# Generated by Django 5.1.4 on 2025-05-04 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Inventory', '0006_alter_itemoperation_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemoperation',
            name='buy_date',
            field=models.DateField(),
        ),
    ]
