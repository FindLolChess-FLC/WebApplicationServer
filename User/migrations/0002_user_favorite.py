# Generated by Django 5.1 on 2024-10-06 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Meta', '0008_remove_comment_writer_alter_comment_content'),
        ('User', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='favorite',
            field=models.ManyToManyField(to='Meta.lolmeta'),
        ),
    ]
