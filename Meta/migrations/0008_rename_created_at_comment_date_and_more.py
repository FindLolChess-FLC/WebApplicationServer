# Generated by Django 5.1 on 2025-03-14 00:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0007_alter_champion_synergy'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='created_at',
            new_name='date',
        ),
        migrations.AlterField(
            model_name='lolmetachampion',
            name='item',
            field=models.ManyToManyField(blank=True, to='Meta.item'),
        ),
    ]
