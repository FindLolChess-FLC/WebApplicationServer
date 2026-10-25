"""Batch-load meta search results and their requested level boards."""
from collections import Counter, defaultdict

from django.db.models import Prefetch, prefetch_related_objects

from .models import Champion, Item, MetaGuide, Synergy
from .serializers import (ChampionSerializer, ItemSerializer, LolMetaSerializer,
                          meta_details_prefetch)


SOURCE_ORDER = {'lolchess': 0, 'opgg': 1, 'tactics': 2}


def _key(name):
    return ''.join(name.split())


def _synergies(roster, synergies):
    counts = Counter()
    for champion, items in roster:
        counts.update(synergy.name for synergy in champion.synergy.all())
        for item in items:
            if '상징' in item.name:
                name = item.name.replace('상징', '').strip()
                if name in synergies:
                    counts[name] += 1
    data = {}
    for name, number in counts.items():
        synergy = synergies[name]
        image = getattr(synergy, 'synergyimg', None)
        data[name] = {'number': number, 'effect': synergy.effect,
                      'img_src': image.img_src if image else None,
                      'sequence': synergy.sequence}
    return [dict(sorted(data.items(), key=lambda row: (
        'unique' in row[1]['sequence'], row[1]['number']), reverse=True))]


def meta_response_data(metas, level=None):
    metas = list(metas)
    if not metas:
        return []
    requested = MetaGuide.objects.filter(level__in=[0, level] if level else [0])
    prefetch_related_objects(metas, meta_details_prefetch(),
                             Prefetch('guides', queryset=requested, to_attr='selected_guides'))
    available_levels = defaultdict(set)
    level_boards = MetaGuide.objects.filter(
        meta_id__in=[meta.pk for meta in metas], level__gt=0,
    ).exclude(champions=[]).values_list('meta_id', 'level')
    for meta_id, board_level in level_boards:
        available_levels[meta_id].add(board_level)
    synergies = {synergy.name: synergy for synergy in
                 Synergy.objects.select_related('synergyimg')}
    slots = [slot for meta in metas for guide in meta.selected_guides
             if guide.level == level and level != meta.default_level
             for slot in guide.champions]
    # Resolve current DB images and descriptions rather than storing serialized snapshots.
    champion_names = {slot['name'] for slot in slots}
    item_names = {name for slot in slots for name in slot['items']}
    champions = {_key(champ.name): champ for champ in Champion.objects.filter(
        name__in=champion_names).select_related('championimg').prefetch_related('synergy')}
    items = {_key(item.name): item for item in Item.objects.filter(
        name__in=item_names).select_related('itemimg')}
    result = []
    for meta in metas:
        guides = sorted(meta.selected_guides, key=lambda guide: SOURCE_ORDER.get(guide.source, 99))
        main_text = '\n\n'.join(dict.fromkeys(
            guide.content for guide in guides if guide.level == 0 and guide.content))
        placements = meta.lolmetachampion_set.all()
        row = {
            'meta': LolMetaSerializer(meta).data,
            'synergys': _synergies([(placed.champion, placed.item.all())
                                   for placed in placements], synergies),
            'detail_info': main_text,
            'selected_level': meta.default_level,
            'available_levels': sorted(available_levels[meta.pk] | {meta.default_level}),
        }
        selected = next((guide for guide in guides
                         if guide.level == level and level != meta.default_level), None)
        if selected is not None:
            board, roster = [], []
            for slot in selected.champions:
                champion = champions.get(_key(slot['name']))
                equipped = [items.get(_key(name)) for name in slot['items']]
                if champion is None or any(item is None for item in equipped):
                    # Never return a partial board if reference data was removed later.
                    break
                placed = {'champion': ChampionSerializer(champion).data,
                          'star': slot['star'], 'location': slot['location']}
                if equipped:
                    placed['item'] = ItemSerializer(equipped, many=True).data
                board.append(placed)
                roster.append((champion, equipped))
            else:
                row['selected_level'] = level
                row['meta']['champions'] = board
                row['synergys'] = _synergies(roster, synergies)
        result.append(row)
    return result
