from collections import defaultdict

from django.db import migrations


LABELS = {
    'lolchess': '롤체지지 덱 설명',
    'opgg': 'OP.GG 덱 설명',
    'tactics': 'tactics.tools 덱 팁',
}


def import_guides(apps, schema_editor):
    """Copy only identified crawler/admin comments; preserve all original comments."""
    Comment = apps.get_model('Meta', 'Comment')
    Guide = apps.get_model('Meta', 'MetaGuide')
    db = schema_editor.connection.alias
    collected = defaultdict(list)
    tracked = {}
    table = 'Crawling_crawledmetacomment'
    if table in schema_editor.connection.introspection.table_names():
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('SELECT source, meta_id, comment_id, position FROM '
                           + schema_editor.quote_name(table) + ' ORDER BY position')
            for source, meta_id, comment_id, position in cursor.fetchall():
                if source in LABELS:
                    tracked[comment_id] = (source, meta_id, position)
    comments = Comment.objects.using(db).filter(writer__is_superuser=True).order_by('pk')
    for comment in comments.iterator():
        content = comment.content
        if comment.pk in tracked:
            source, meta_id, position = tracked[comment.pk]
            if meta_id != comment.lol_meta_id:
                continue
        else:
            source = next((key for key, label in LABELS.items()
                           if content.startswith(f'[{label}]')), None)
            if source is None:
                continue
            position = 0
        prefix = f'[{LABELS[source]}]'
        if content.startswith(prefix):
            content = content[len(prefix):].lstrip()
        if content.strip():
            collected[(comment.lol_meta_id, source)].append((position, content.strip()))
    for (meta_id, source), parts in collected.items():
        content = '\n\n'.join(dict.fromkeys(text for _, text in sorted(parts, key=lambda p: p[0])))
        Guide.objects.using(db).get_or_create(
            meta_id=meta_id, source=source, level=0, defaults={'content': content})


class Migration(migrations.Migration):
    dependencies = [('Meta', '0010_alter_item_item1_alter_item_item2_metaguide')]
    operations = [migrations.RunPython(import_guides, migrations.RunPython.noop)]
