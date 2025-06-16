from django.core.management.base import BaseCommand
from Crawling.img_crawl.save_synergy import save_synergy
from Crawling.img_crawl.save_augment import save_augment
from Crawling.img_crawl.save_champion import save_champion
from Crawling.img_crawl.save_item import save_item


class Command(BaseCommand):

    def handle(self, *args, **options):
        save_item()
        save_champion()
        save_augment()
        save_synergy()