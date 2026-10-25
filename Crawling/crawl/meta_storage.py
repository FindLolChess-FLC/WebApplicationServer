"""Persist representative meta boards shared by crawler commands."""
from collections import Counter

from django.db import transaction

from Crawling.utils import reroll_lv
from Meta.models import LolMeta, LolMetaChampion


def name_key(name):
    return ''.join(name.split())


def save_records(records, champions, items):
    with transaction.atomic():
        for record in records:
            meta, _ = LolMeta.objects.get_or_create(title=record['title'])
            LolMetaChampion.objects.filter(meta=meta).delete()
            stars_by_cost = Counter()
            unit_count = 0
            for slot in record['champions']:
                champion = champions[name_key(slot['name'])]
                placed = LolMetaChampion.objects.create(
                    meta=meta, champion=champion,
                    star=slot['star'], location=slot['location'])
                placed.item.set([items[name_key(name)] for name in slot['items']])
                if champion.price > 0:
                    unit_count += 1
                    stars_by_cost[champion.price] += slot['star']
            max_stars = max(stars_by_cost.values())
            dominant_cost = max(cost for cost, stars in stars_by_cost.items()
                                if stars == max_stars)
            meta.reroll_lv = reroll_lv(dominant_cost)
            meta.default_level = record.get('default_level', min(10, max(1, unit_count)))
            meta.save(update_fields=['reroll_lv', 'default_level'])
