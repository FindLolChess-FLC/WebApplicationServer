"""Collect LoLCHESS metas using existing champion/item references."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from Crawling.crawl.lolchess_crawling import collect_lolchess_meta
from Crawling.crawl.meta_details import sync_meta_details
from Crawling.crawl.meta_storage import name_key, save_records
from Meta.models import Champion, Item


class Command(BaseCommand):
    help = '기존 기초 데이터를 사용해 롤체지지 메타·설명·레벨 배치를 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--season', type=int, default=18)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        if options['season'] < 1:
            raise CommandError('시즌은 양수여야 합니다.')
        try:
            records = collect_lolchess_meta(season=options['season'], include_details=True)
        except Exception as exc:
            raise CommandError(f'lolchess.gg 수집 실패: {exc}') from exc
        champions = {name_key(champion.name): champion for champion in Champion.objects.all()}
        items = {name_key(item.name): item for item in Item.objects.all()}
        missing_champions = {name_key(slot['name']) for record in records
                            for slot in record['champions']} - champions.keys()
        missing_items = {name_key(name) for record in records for slot in record['champions']
                         for name in slot['items']} - items.keys()
        if missing_champions or missing_items:
            raise CommandError(f'기초 DB 참조 누락: 챔피언 {sorted(missing_champions)}, '
                               f'아이템 {sorted(missing_items)}')
        self.stdout.write(f'메타 {len(records)}개 수집·참조 확인 완료')
        if options['dry_run']:
            sync_meta_details([('lolchess', records)], dry_run=True, write=self.stdout.write)
            return
        with transaction.atomic():
            save_records(records, champions, items)
            sync_meta_details([('lolchess', records)], write=self.stdout.write)
        self.stdout.write(self.style.SUCCESS(f'메타 {len(records)}개 및 상세 정보 DB 반영 완료'))
