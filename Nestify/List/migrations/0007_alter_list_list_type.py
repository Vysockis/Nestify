# Generated by Django 5.1.4 on 2025-02-19 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('List', '0006_list_amount_list_category_list_receipt_pdf_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='list',
            name='list_type',
            field=models.CharField(
                choices=[
                    ('GROCERY',
                     'Grocery'),
                    ('TASK',
                     'Task'),
                    ('MEAL',
                     'Meal'),
                    ('FINANCE',
                     'Finance'),
                    ('OTHER',
                     'Other')],
                default='OTHER',
                max_length=20),
        ),
    ]
