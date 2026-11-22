from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CrawledMetaComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=20)),
                ('meta_id', models.BigIntegerField()),
                ('position', models.PositiveIntegerField()),
                ('comment_id', models.BigIntegerField(unique=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name='crawledmetacomment',
            constraint=models.UniqueConstraint(
                fields=('source', 'meta_id', 'position'),
                name='unique_crawled_comment_position',
            ),
        ),
    ]
