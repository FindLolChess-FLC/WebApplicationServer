from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('Meta', '0008_rename_created_at_comment_date_and_more')]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='content',
            field=models.TextField(),
        ),
    ]
