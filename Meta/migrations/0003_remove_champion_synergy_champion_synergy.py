# Generated by Django 5.1 on 2024-09-15 00:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0002_synergy_effect'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='champion',
            name='synergy',
        ),
        migrations.AddField(
            model_name='champion',
            name='synergy',
            field=models.ManyToManyField(to='Meta.synergy'),
        ),
    ]
