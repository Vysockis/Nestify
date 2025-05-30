# Generated by Django 5.1.4 on 2025-05-07 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Family', '0015_familymember_points'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('invite', 'Family Invitation'), ('request', 'Join Request'), ('system', 'System Notification'), ('general', 'General Notification'), ('task_assigned', 'Task Assignment')], default='general', max_length=20),
        ),
    ]
