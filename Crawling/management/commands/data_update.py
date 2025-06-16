from django.core.management.base import BaseCommand
from Crawling.data_update.update_item import update_item


class Command(BaseCommand):

    def handle(self, *args, **options):
        update_item()