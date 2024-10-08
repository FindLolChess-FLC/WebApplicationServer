# Generated by Django 5.1 on 2024-09-18 20:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0003_remove_champion_synergy_champion_synergy'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('effect', models.CharField(max_length=500)),
                ('item1', models.CharField(max_length=25)),
                ('item2', models.CharField(max_length=25)),
            ],
        ),
        migrations.RemoveField(
            model_name='lolmetachampion',
            name='item',
        ),
        migrations.AlterField(
            model_name='synergy',
            name='name',
            field=models.CharField(max_length=15),
        ),
        migrations.CreateModel(
            name='ItemImg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_src', models.CharField(max_length=255)),
                ('item', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Meta.item')),
            ],
        ),
        migrations.AddField(
            model_name='lolmetachampion',
            name='item',
            field=models.ManyToManyField(to='Meta.item'),
        ),
    ]
