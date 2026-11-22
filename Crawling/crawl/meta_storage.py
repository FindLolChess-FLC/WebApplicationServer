"""Persist representative meta boards shared by crawler commands."""
from collections import Counter

from django.db import transaction

from Crawling.utils import reroll_lv
from Meta.models import LolMeta, LolMetaChampion, MetaGuide


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


def promote_one_star_board(slots, prices):
    """OP.GG level tabs omit star marks, so an all 1-star board is read as 2-star."""
    units = [slot for slot in slots if prices.get(name_key(slot['name']), 1) > 0]
    if not units or any(slot['star'] != 1 for slot in units):
        return False
    for slot in units:
        slot['star'] = 2
    return True


def promote_opgg_boards(records, prices):
    """Correct collected OP.GG boards whose stars were not observed on the page."""
    boards = (board for record in records for board in (record, *record.get('guides', [])))
    return sum(promote_one_star_board(board['champions'], prices) for board in boards
               if not board.get('stars_observed'))


def promote_stored_opgg_guides(prices, synced=()):
    """Correct OP.GG level boards saved earlier without star marks; skip this run's boards."""
    fresh = [meta_id for meta_id, source in synced if source == 'opgg']
    promoted = 0
    for guide in MetaGuide.objects.filter(source='opgg', level__gt=0).exclude(
            champions=[]).exclude(meta_id__in=fresh):
        if promote_one_star_board(guide.champions, prices):
            guide.save(update_fields=['champions'])
            promoted += 1
    return promoted
