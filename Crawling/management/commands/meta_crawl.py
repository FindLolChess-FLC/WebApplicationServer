from django.core.management.base import BaseCommand
from Crawling.crawl.lolchess_crawling import lolchess_crawling

class Command(BaseCommand):

    def handle(self, *args, **options):
        lolchess_crawling()
