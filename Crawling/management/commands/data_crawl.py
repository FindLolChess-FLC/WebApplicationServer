from django.core.management.base import BaseCommand
from Crawling.crawl.synergy_crawling import synergy_crawling
from Crawling.crawl.champ_crawling import champion_crawling
from Crawling.crawl.item_crawling import item_crawling
from Crawling.crawl.augmenter_crawling import augmenter_crawling


class Command(BaseCommand):

    def handle(self, *args, **options):
        synergy_crawling()
        champion_crawling()
        item_crawling()
        augmenter_crawling()