from django.core.management.base import BaseCommand
from Crawling.crawl.opgg_crawling import opgg_crawling
from Crawling.crawl.lolchess_crawling import lolchess_crawling
from Crawling.utils import reroll_lv
from Meta.models import * 


class Command(BaseCommand):

    def handle(self, *args, **options):
        lolchess = lolchess_crawling()
        opgg = opgg_crawling()

        meta_data = {}

        # for data in meta_data:
        #     meta, craeted = LolMeta.objects.get_or_create(title = data)

        #     champ_star = {1:0, 2:0, 3:0, 4:0, 5:0} 
        #     for champ_name in meta_data[data]['챔프']:
        #         champion, created = LolMetaChampion.objects.get_or_create(meta = meta, 
        #                                                     champion = Champion.objects.get(name = champ_name),
        #                                                     star = meta_data[data]['별'][champ_name], 
        #                                                     location = meta_data[data]['위치'][champ_name])
                
        #         price = Champion.objects.get(name = champ_name).price

        #         champ_star[price] += meta_data[data]['별'][champ_name]

        #         champ_item = meta_data[data]['아이템'].get(champ_name, [])
        #         if len(champ_item) > 0 :
        #             for item in champ_item:
        #                 if Item.objects.filter(name=item).exists():
        #                     champion.item.add(Item.objects.filter(name=item).first())

        #     max_value = max(champ_star.values())
        #     max_keys = [key for key, value in champ_star.items() if value == max_value]

        #     meta.reroll_lv = reroll_lv(max(max_keys))
        #     meta.save()
