"""Collect all three meta sites, deduplicate by champions, and save valid boards."""
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from Crawling.crawl.lolchess_crawling import collect_lolchess_meta
from Crawling.crawl.opgg_crawling import collect_opgg_meta
from Crawling.crawl.tactics_crawling import collect_tactics_meta
from Crawling.crawl.meta_details import sync_meta_details
from Crawling.crawl.meta_storage import name_key, save_records
from Crawling.utils import remove_duplicates_data
from Meta.models import Champion, Item, LolMeta, LolMetaChampion


def comparable_champions(record, champions):
    """Use known, purchasable champions; summons cannot distort similarity."""
    return sorted({name_key(slot['name']) for slot in record['champions']
                   if name_key(slot['name']) in champions
                   and champions[name_key(slot['name'])].price > 0})


def valid_board(record):
    slots = record['champions']
    locations = [slot['location'] for slot in slots]
    return (record.get('complete', True) and 5 <= len(slots) <= 28
            and len(locations) == len(set(locations))
            and all(1 <= location <= 28 for location in locations)
            and all(1 <= slot['star'] <= 3 for slot in slots))


def unique_meta_title(title, used):
    if title not in used:
        return title
    for number in range(2, 1000):
        suffix = f' {number}'
        candidate = title[:50 - len(suffix)] + suffix
        if candidate not in used:
            return candidate
    raise ValueError(f'중복 덱 제목을 구별할 수 없습니다: {title}')


class Command(BaseCommand):
    help = 'lolchess.gg, OP.GG, tactics.tools 메타 덱을 수집하고 유사 덱을 제외해 DB에 저장합니다.'

    def progress(self, message):
        self.stdout.write(message)
        self.stdout.flush()

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--similarity', type=float, default=0.85)

    def handle(self, *args, **options):
        threshold = options['similarity']
        if not 0 < threshold <= 1:
            raise CommandError('유사도 기준은 0보다 크고 1 이하여야 합니다.')

        # Collect all sites before changing the database. Site order determines
        # which representative survives when their champion rosters are similar.
        sources = []
        for index, (name, collector) in enumerate((
            ('lolchess', lambda: collect_lolchess_meta(include_details=True)),
            ('opgg', collect_opgg_meta),
            ('tactics', collect_tactics_meta),
        ), start=1):
            self.progress(f'[{index}/7] {name}: 메타·상세 정보 수집 시작')
            try:
                records = collector()
            except Exception as exc:
                raise CommandError(f'{name} 수집 실패: {exc}') from exc
            if not records:
                raise CommandError(f'{name}에서 메타 덱을 찾지 못했습니다.')
            sources.append((name, records))
            self.progress(f'[{index}/7] {name}: {len(records)}개 수집 완료')

        self.progress('[4/7] 유사도 검사 시작')
        champions = {name_key(champion.name): champion for champion in Champion.objects.all()}
        prices = {name: champion.price for name, champion in champions.items()}
        items = {name_key(item.name): item for item in Item.objects.all()}
        existing = defaultdict(set)
        for placed in LolMetaChampion.objects.select_related('champion').filter(champion__price__gt=0):
            existing[placed.meta_id].add(name_key(placed.champion.name))
        merged = {f'db:{meta_id}': {'챔프': sorted(roster)}
                  for meta_id, roster in existing.items() if len(roster) >= 5}
        known_count = len(merged)
        too_few = 0
        for source, records in sources:
            incoming = {}
            for index, record in enumerate(sorted(records, key=lambda row: not row.get('complete', True))):
                roster = comparable_champions(record, champions)
                if len(roster) < 5:
                    too_few += 1
                    continue
                incoming[f'{source}:{index}'] = {
                    '챔프': roster, 'record': record,
                }
            before = len(merged)
            merged = remove_duplicates_data(merged, incoming, threshold, prices)
            self.stdout.write(f'{source}: 유사 덱 {len(incoming) - (len(merged) - before)}개 제외')

        self.progress('[4/7] 유사도 검사 완료')
        self.progress('[5/7] 배치·DB 참조 검증 시작')
        titles = set(LolMeta.objects.values_list('title', flat=True))
        ready, incomplete, missing, renamed = [], [], [], []
        for value in list(merged.values())[known_count:]:
            record = value['record']
            title = record['title']
            if not valid_board(record):
                incomplete.append(title)
                continue
            missing_champs = {name_key(slot['name']) for slot in record['champions']
                              if name_key(slot['name']) not in champions}
            missing_items = {name_key(name) for slot in record['champions'] for name in slot['items']
                             if name_key(name) not in items}
            if missing_champs or missing_items:
                missing.append((record, missing_champs, missing_items))
                continue
            saved_title = unique_meta_title(title, titles)
            if saved_title != title:
                renamed.append((title, saved_title))
            ready.append({**record, 'title': saved_title})
            titles.add(saved_title)

        self.stdout.write(f'비교 가능한 챔피언 부족 {too_few}개, 배치 미확인 {len(incomplete)}개, '
                          f'참조 누락 {len(missing)}개, 제목 구분 {len(renamed)}개, '
                          f'저장 대상 {len(ready)}개')
        if incomplete:
            self.stdout.write('배치 미확인: ' + ', '.join(incomplete))
        for record, champ_names, item_names in missing:
            self.stdout.write(f'참조 누락 {record["title"]}: 챔피언 {sorted(champ_names)}, '
                              f'아이템 {sorted(item_names)}')
        for old, new in renamed:
            self.stdout.write(f'제목 구분: {old} → {new}')
        self.progress('[5/7] 배치·DB 참조 검증 완료')
        if options['dry_run']:
            sync_meta_details(sources, dry_run=True, write=self.progress)
            self.stdout.write('신규 메타의 상세 정보는 실제 저장 시 함께 연결됩니다.')
            return
        try:
            with transaction.atomic():
                self.progress('[6/7] 신규 메타 DB 반영 시작')
                if ready:
                    save_records(ready, champions, items)
                self.progress('[6/7] 신규 메타 DB 반영 완료')
                self.progress('[7/7] 상세 설명·레벨 배치 DB 반영 시작')
                sync_meta_details(sources, write=self.progress)
                self.progress('[7/7] 상세 설명·레벨 배치 DB 반영 완료')
        except ValueError as exc:
            raise CommandError(f'상세 정보 DB 반영 실패: {exc}') from exc
        self.stdout.write(self.style.SUCCESS(f'신규 메타 덱 {len(ready)}개 DB 저장 완료'))
