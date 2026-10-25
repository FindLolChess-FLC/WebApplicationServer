"""Match source guides to stored metas and synchronize their level variants."""
from django.db import transaction

from Meta.models import Champion, Item, LolMeta, LolMetaChampion, MetaGuide
from Crawling.crawl.meta_storage import name_key


SOURCES = ('lolchess', 'opgg', 'tactics')


def match_meta(record, metas, rosters):
    title = record['title'].strip()
    source_roster = {name_key(slot['name']) for slot in record['champions']}
    scored = []
    for meta in metas:
        roster = rosters.get(meta.pk, set())
        union = source_roster | roster
        similarity = len(source_roster & roster) / len(union) if union else 0
        base, _, suffix = meta.title.rpartition(' ')
        numbered_title = (suffix.isdecimal() and int(suffix) >= 2
                          and base == title[:50 - len(suffix) - 1])
        same_title = meta.title == title or numbered_title
        if similarity >= (0.7 if same_title else 0.9):
            scored.append((same_title, similarity, meta.title == title, meta))
    scored.sort(key=lambda row: row[:3], reverse=True)
    if len(scored) > 1 and scored[0][:3] == scored[1][:3]:
        return None
    return scored[0][3] if scored else None


def record_guides(source, record):
    guides = list(record.get('guides', []))
    if source == 'lolchess':
        return guides
    content = (record.get('description') or '').strip() if source == 'opgg' else (
        '\n'.join(record.get('tips') or []))
    if content:
        guides.append({'level': 0, 'content': content, 'champions': []})
    return guides


def sync_meta_details(sources, *, dry_run=False, write=print):
    metas = list(LolMeta.objects.all())
    rosters = {meta.pk: set() for meta in metas}
    for meta_id, name in LolMetaChampion.objects.values_list('meta_id', 'champion__name'):
        rosters[meta_id].add(name_key(name))
    champions = {name_key(name): name for name in Champion.objects.values_list('name', flat=True)}
    items = {name_key(name): name for name in Item.objects.values_list('name', flat=True)}
    ready = {}
    for source, records in sources:
        for record in records:
            guides = record_guides(source, record)
            if not guides:
                continue
            meta = match_meta(record, metas, rosters)
            if meta is None:
                write(f'{source}: 설명 연결 건너뜀: {record["title"]} (대응 덱 없음/모호함)')
                continue
            identity = (meta.pk, source)
            if identity in ready:
                write(f'{source}: 설명 연결 건너뜀: {record["title"]} (같은 메타의 중복 가이드)')
                continue
            valid = []
            for guide in guides:
                slots = guide['champions']
                missing = {name_key(slot['name']) for slot in slots} - champions.keys()
                missing_items = ({name_key(name) for slot in slots for name in slot['items']}
                                 - items.keys())
                if missing or missing_items:
                    write(f'{record["title"]} Lv.{guide["level"]} 건너뜀: '
                          f'챔피언 참조 누락 {sorted(missing)}, '
                          f'아이템 참조 누락 {sorted(missing_items)}')
                    continue
                valid.append({**guide, 'champions': [
                    {'name': champions[name_key(slot['name'])],
                     'star': slot['star'], 'location': slot['location'],
                     'items': [items[name_key(name)] for name in slot['items']]}
                    for slot in slots]})
            ready[identity] = (record, valid)
    total = sum(len(guides) for _, guides in ready.values())
    levels = sum(guide['level'] > 0 for _, guides in ready.values() for guide in guides)
    write(f'상세 설명 연결 {len(ready)}개, 저장 항목 {total}개 (레벨 배치 {levels}개)')
    if dry_run:
        return
    with transaction.atomic():
        for (meta_id, source), (record, guides) in ready.items():
            if (source == 'lolchess' and record.get('default_level')
                    and rosters[meta_id] == {name_key(slot['name'])
                                            for slot in record['champions']}):
                LolMeta.objects.filter(pk=meta_id).update(default_level=record['default_level'])
            MetaGuide.objects.filter(meta_id=meta_id, source=source).exclude(
                level__in=[guide['level'] for guide in guides]).delete()
            for guide in guides:
                MetaGuide.objects.update_or_create(
                    meta_id=meta_id, source=source, level=guide['level'],
                    defaults={
                        'source_id': str(record.get('id', '')),
                        'source_url': record.get('source_url', ''),
                        'content': guide['content'], 'champions': guide['champions'],
                    })
    write('상세 설명·레벨 배치 DB 반영 완료')
