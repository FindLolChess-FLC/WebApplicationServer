# Generated by Django 5.1 on 2024-11-21 18:03

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Augmenter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('effect', models.CharField(max_length=500)),
                ('tier', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Champion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('kor_name', models.CharField(max_length=25)),
                ('effect', models.CharField(max_length=500)),
                ('item1', models.CharField(max_length=25)),
                ('kor_item1', models.CharField(max_length=25)),
                ('item2', models.CharField(max_length=25)),
                ('kor_item2', models.CharField(max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='ItemImg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_src', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='LolMeta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('like_count', models.IntegerField(default=0)),
                ('dislike_count', models.IntegerField(default=0)),
                ('reroll_lv', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='LolMetaChampion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('star', models.IntegerField()),
                ('location', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MetaReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_like', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Synergy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
                ('effect', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='SynergyImg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_src', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='AugmenterImg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_src', models.CharField(max_length=255)),
                ('augmenter', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='Meta.augmenter')),
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
    ]
