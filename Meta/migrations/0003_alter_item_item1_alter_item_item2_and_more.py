# Generated by Django 5.1 on 2024-11-21 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='item1',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='item',
            name='item2',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='item',
            name='kor_item1',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='item',
            name='kor_item2',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='item',
            name='kor_name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='item',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
