# Generated by Django 5.1 on 2024-08-26 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0004_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='token',
            field=models.CharField(max_length=255),
        ),
    ]
