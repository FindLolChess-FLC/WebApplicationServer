from django.core.management.base import BaseCommand
from Crawling.crawl.synergy_crawling import synergy_crawling
from Crawling.crawl.champ_crawling import champion_crawling
from Crawling.crawl.item_crawling import item_crawling
from Crawling.crawl.augmenter_crawling import augmenter_crawling


class Command(BaseCommand):
    def progress(self, message, *, complete=False):
        self.stdout.write(self.style.SUCCESS(message) if complete else message)
        self.stdout.flush()

    def handle(self, *args, **options):
        stages = (
            ('시너지', synergy_crawling),
            ('챔피언', champion_crawling),
            ('아이템', item_crawling),
            ('증강체', augmenter_crawling),
        )
        for index, (name, collector) in enumerate(stages, start=1):
            self.progress(f'[{index}/{len(stages)}] {name} 수집 시작')
            records = collector()
            self.progress(f'[{index}/{len(stages)}] {name} 완료: {len(records)}개 수집·DB 반영',
                          complete=True)
