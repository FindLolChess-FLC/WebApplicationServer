# Generated by Django 5.1 on 2024-09-14 16:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Champion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='LolMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('win_rate', models.DecimalField(decimal_places=2, max_digits=5)),
                ('like_count', models.IntegerField(default=0)),
                ('dislike_count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Synergy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ChampionImg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_src', models.CharField(max_length=255)),
                ('champion', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Meta.champion')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('writer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('lol_meta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.lolmeta')),
            ],
        ),
        migrations.CreateModel(
            name='LolMetaChampion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('star', models.IntegerField()),
                ('location', models.IntegerField()),
                ('item', models.CharField(max_length=50)),
                ('champion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.champion')),
                ('meta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.lolmeta')),
            ],
        ),
        migrations.AddField(
            model_name='champion',
            name='synergy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Meta.synergy'),
        ),
        migrations.CreateModel(
            name='SynergyImg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_src', models.CharField(max_length=255)),
                ('synergy', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Meta.synergy')),
            ],
        ),
    ]