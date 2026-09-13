from django.core.management.base import BaseCommand
from Crawling.crawl.synergy_crawling import synergy_crawling, save_synergies
from Crawling.crawl.champ_crawling import champion_crawling, save_champions
from Crawling.crawl.item_crawling import item_crawling, save_items
from Crawling.crawl.augmenter_crawling import augmenter_crawling, save_augments
from Crawling.crawl.cloudinary_assets import resolve_existing_urls


class Command(BaseCommand):
    def progress(self, message, *, complete=False):
        self.stdout.write(self.style.SUCCESS(message) if complete else message)
        self.stdout.flush()

    def handle(self, *args, **options):
        stages = (
            ('시너지', 'synergy', synergy_crawling, save_synergies),
            ('챔피언', 'champion', champion_crawling, save_champions),
            ('아이템', 'item', item_crawling, save_items),
            ('증강체', 'augment', augmenter_crawling, save_augments),
        )
        for index, (name, category, collector, saver) in enumerate(stages, start=1):
            self.progress(f'[{index}/{len(stages)}] {name} 수집 시작')
            records = collector(dry_run=True)
            self.progress(f'[{index}/{len(stages)}] {name} 수집 완료: {len(records)}개; Cloudinary URL 조회 시작')
            records = resolve_existing_urls(category, records)
            self.progress(f'[{index}/{len(stages)}] {name} Cloudinary URL 조회 완료; DB 반영 시작')
            saver(records)
            self.progress(f'[{index}/{len(stages)}] {name} 완료: {len(records)}개 DB 반영',
                          complete=True)
