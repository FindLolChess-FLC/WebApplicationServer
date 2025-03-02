from django.core.management.base import BaseCommand
from Crawling.crawl.opgg_crawling import opgg_crawling
from Crawling.crawl.lolchess_crawling import lolchess_crawling
from Crawling.crawl.tactics_crawling import tactics_crawling
from Crawling.utils import reroll_lv, jacaard_similarity, remove_duplicates_data
from Meta.models import * 

class Command(BaseCommand):

    def handle(self, *args, **options):
        lolchess = lolchess_crawling()
        opgg = opgg_crawling()
        tactics = tactics_crawling()

        first_merged_data = remove_duplicates_data(lolchess,opgg)
        final_merged_data = remove_duplicates_data(first_merged_data,tactics)
        merge_duplicate_keys = set()

        db_meta_data = LolMeta.objects.all()
        db_meta_champion = []

        if db_meta_data:
            for db_meta in db_meta_data:
                db_meta_champion.append([meta_champ.champion.name for meta_champ in LolMetaChampion.objects.select_related('champion').filter(meta=db_meta)])

        for merge_key, merge_value in final_merged_data.items():
            for db_meta in db_meta_champion:
                if jacaard_similarity(merge_value['챔프'], db_meta) == 1:
                    merge_duplicate_keys.add(merge_key)
                    break 
        
        for merge_key in merge_duplicate_keys:
            del final_merged_data[merge_key]

        meta_data = final_merged_data

        for data in meta_data:
            meta, created = LolMeta.objects.get_or_create(title = data)
            
            if not created:
                continue

            champ_star = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0} 
            for champ_name in meta_data[data]['챔프']:
                champion, created = LolMetaChampion.objects.get_or_create(meta = meta, 
                                                            champion = Champion.objects.get(name = champ_name.replace(' ', '')),
                                                            star = meta_data[data]['별'][champ_name], 
                                                            location = meta_data[data]['위치'][champ_name])
                
                price = Champion.objects.get(name = champ_name.replace(' ', '')).price

                champ_star[price] += meta_data[data]['별'][champ_name]

                champ_item = meta_data[data]['아이템'].get(champ_name, [])
                if len(champ_item) > 0 :
                    for item in champ_item:
                        if Item.objects.filter(name=item).exists():
                            champion.item.add(Item.objects.filter(name=item).first())

            max_value = max(champ_star.values())
            max_keys = [key for key, value in champ_star.items() if value == max_value]

            meta.reroll_lv = reroll_lv(max(max_keys))
            meta.save()
    