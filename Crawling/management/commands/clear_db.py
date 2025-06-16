from Meta.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        Synergy.objects.all().delete()
        SynergyImg.objects.all().delete()
        Augmenter.objects.all().delete()
        AugmenterImg.objects.all().delete()
        Item.objects.all().delete()
        ItemImg.objects.all().delete()
        Champion.objects.all().delete()
        ChampionImg.objects.all().delete()
        LolMeta.objects.all().delete()
        MetaReaction.objects.all().delete()
        LolMetaChampion.objects.all().delete()
        Comment.objects.all().delete()

        print('DB 초기화 완료')

