# Generated by Django 5.1 on 2024-12-30 02:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0006_remove_item_kor_item1_remove_item_kor_item2_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='champion',
            name='synergy',
            field=models.ManyToManyField(blank=True, to='Meta.synergy'),
        ),
    ]