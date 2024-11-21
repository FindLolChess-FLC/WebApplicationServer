# Generated by Django 5.1 on 2024-11-21 18:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Meta', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='writer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='itemimg',
            name='item',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Meta.item'),
        ),
        migrations.AddField(
            model_name='comment',
            name='lol_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.lolmeta'),
        ),
        migrations.AddField(
            model_name='lolmetachampion',
            name='champion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.champion'),
        ),
        migrations.AddField(
            model_name='lolmetachampion',
            name='item',
            field=models.ManyToManyField(to='Meta.item'),
        ),
        migrations.AddField(
            model_name='lolmetachampion',
            name='meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.lolmeta'),
        ),
        migrations.AddField(
            model_name='metareaction',
            name='lol_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.lolmeta'),
        ),
        migrations.AddField(
            model_name='metareaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='champion',
            name='synergy',
            field=models.ManyToManyField(to='Meta.synergy'),
        ),
        migrations.AddField(
            model_name='synergyimg',
            name='synergy',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Meta.synergy'),
        ),
    ]