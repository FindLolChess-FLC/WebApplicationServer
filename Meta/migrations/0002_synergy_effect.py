# Generated by Django 5.1 on 2024-09-14 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='synergy',
            name='effect',
            field=models.CharField(default=1, max_length=500),
            preserve_default=False,
        ),
    ]
