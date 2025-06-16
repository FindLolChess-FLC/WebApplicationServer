from django.core.management.base import BaseCommand
from Crawling.data_update.check_duplicate import find_duplicate_lolmeta


class Command(BaseCommand):

    def handle(self, *args, **options):
        find_duplicate_lolmeta()