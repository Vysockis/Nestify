# Generated by Django 5.1.4 on 2025-01-13 16:59

import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Family', '0002_alter_familycode_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pocket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10)),
            ],
            options={
                'verbose_name': 'Pocket',
                'verbose_name_plural': 'Pockets',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Family.family')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categorys',
            },
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('datetime', models.DateTimeField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Finance.category')),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Family.family')),
            ],
            options={
                'verbose_name': 'Operation',
                'verbose_name_plural': 'Operations',
            },
        ),
        migrations.CreateModel(
            name='OperationItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('qty', models.IntegerField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Finance.operation')),
            ],
            options={
                'verbose_name': 'OperationItem',
                'verbose_name_plural': 'OperationItems',
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('wallet_type', models.CharField(choices=[('MAIN', 'Main'), ('SAVING', 'Saving')], default='MAIN', max_length=20)),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Family.family')),
            ],
            options={
                'verbose_name': 'Wallet',
                'verbose_name_plural': 'Wallets',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deposit', models.BooleanField(default=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('pocket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Finance.pocket', verbose_name='')),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Finance.wallet')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
            },
        ),
        migrations.AddField(
            model_name='pocket',
            name='wallet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Finance.wallet'),
        ),
        migrations.AddField(
            model_name='operation',
            name='wallet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Finance.wallet', verbose_name=''),
        ),
    ]
