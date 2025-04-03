from Meta.models import *
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 외래 키 참조 데이터 먼저 삭제
        MetaReaction.objects.all().delete()
        LolMetaChampion.objects.all().delete()
        Comment.objects.all().delete()

        ChampionImg.objects.all().delete()
        Champion.objects.all().delete()

        ItemImg.objects.all().delete()
        Item.objects.all().delete()

        AugmenterImg.objects.all().delete()
        Augmenter.objects.all().delete()

        SynergyImg.objects.all().delete()
        Synergy.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('모든 데이터를 성공적으로 삭제했습니다.'))
