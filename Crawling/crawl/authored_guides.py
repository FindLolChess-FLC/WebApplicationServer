"""Portable, data-only descriptions matched against an existing meta board."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from django.core.management.base import CommandError


FORMAT = 'flc-meta-guides-v1'


def name_key(value):
    return ''.join(unicodedata.normalize('NFKC', value).split()).casefold()


def board_data(meta):
    return sorted([
        {'name': placed.champion.name, 'star': placed.star,
         'location': placed.location,
         'items': sorted(item.name for item in placed.item.all())}
        for placed in meta.lolmetachampion_set.all()
    ], key=lambda slot: slot['location'])


def board_key(board):
    return sorted((name_key(slot['name']), slot['star'], slot['location'],
                   tuple(sorted(name_key(item) for item in slot['items'])))
                  for slot in board)


def title_family(title):
    if not re.search(r'\b(?:rush|fast|lv|level)\s+\d+$', title, re.I):
        match = re.search(r'\s+(\d+)$', title)
        if match and int(match[1]) >= 2:
            title = title[:match.start()]
    return name_key(title)


DEFENSIVE_ITEMS = {name_key(name) for name in (
    '워모그의 갑옷', '가고일 돌갑옷', '정령의 형상', '수호자의 맹세',
    '저녁갑주', '태양불꽃 망토', '굳건한 심장', '덤불 조끼', '용의 발톱',
    '크라운가드', '적응형 투구', '구원')}


def _profile(title, board, prices):
    roster = {name_key(slot['name']): slot for slot in board
              if prices.get(name_key(slot['name']), 1) > 0}
    equipped = {name for name, slot in roster.items() if slot['items']}
    named = {name for name in equipped if name in name_key(title)}
    attackers = {name for name in equipped
                 if sum(name_key(item) not in DEFENSIVE_ITEMS
                        and '상징' not in item for item in roster[name]['items']) >= 2}
    anchors = named or attackers
    emblems = Counter((name_key(slot['name']), name_key(item))
                      for slot in board for item in slot['items'] if '상징' in item)
    conditions = {name_key(value) for value in re.findall(r'\[([^]]+)\]', title)
                  if name_key(value) != '상징'}
    return roster, anchors, emblems, conditions


def match_guide(meta, entries, prices, *, strict=False):
    """Match operating plans, without equating unit overlap with battle strength."""
    board = board_data(meta)
    key = board_key(board)
    roster, anchors, emblems, conditions = _profile(meta.title, board, prices)
    scored, rejected = [], []
    for entry in entries:
        same_title = name_key(entry['title']) == name_key(meta.title)
        same_family = title_family(entry['title']) == title_family(meta.title)
        exact = key == board_key(entry['board']) and meta.default_level == entry['default_level']
        if strict:
            if same_title and exact:
                scored.append((1.0, True, True, entry))
            continue
        source, source_anchors, source_emblems, source_conditions = _profile(
            entry['title'], entry['board'], prices)
        union = source.keys() | roster.keys()
        common = source.keys() & roster.keys()
        overlap = len(common) / len(union) if union else 0
        reason = None
        if ('요약' in entry['title'] or '요약' in meta.title):
            if not (same_family and exact):
                reason = '요약 자료 구성 다름'
        elif source_conditions != conditions:
            reason = '필수 증강 조건 다름'
        elif source_emblems != emblems:
            reason = '상징 종류 또는 장착 유닛 다름'
        elif abs(meta.default_level - entry['default_level']) > 1:
            reason = '대표 레벨 차이 큼'
        elif not source_anchors or not source_anchors <= roster.keys():
            reason = '주력 유닛 누락'
        elif not anchors or not anchors <= source.keys():
            reason = '주력 유닛 변경'
        elif any((source[name]['star'] == 3) != (roster[name]['star'] == 3)
                 for name in source_anchors | anchors):
            reason = '주력 3성 리롤 목표 다름'
        elif any(name in name_key(entry['content'].partition('아이템 우선순위')[2]
                                  .partition('레벨업 운영')[0])
                 for name in source.keys() - roster.keys()):
            reason = '아이템 운영에 필요한 유닛 누락'
        elif overlap < (0.75 if same_family else 0.9):
            reason = '챔피언 구성 차이 큼'
        if reason:
            rejected.append((overlap, same_title, entry['title'], reason))
            continue
        # Location is deliberately excluded. Ordinary item swaps only break ties.
        stars = (sum(source[name]['star'] == roster[name]['star'] for name in common)
                 / len(common)) if common else 0
        left_items = {(name, name_key(item)) for name, slot in source.items()
                      for item in slot['items']}
        right_items = {(name, name_key(item)) for name, slot in roster.items()
                       for item in slot['items']}
        item_union = left_items | right_items
        items = len(left_items & right_items) / len(item_union) if item_union else 1
        score = 0.8 * overlap + 0.1 * stars + 0.1 * items
        scored.append((score, exact, same_title, entry))
    if not scored:
        nearest = max(rejected, key=lambda row: row[:2], default=None)
        reason = f'{nearest[3]}; 가까운 원본: {nearest[2]}' if nearest else '대응 설명 없음'
        return None, reason
    scored.sort(key=lambda row: row[:3], reverse=True)
    best = scored[0]
    if len(scored) > 1:
        second = scored[1]
        # Prefer a unique exact board or, within near-equal scores, the exact title.
        if not (best[1] and not second[1]):
            exact_titles = [row for row in scored if row[2] and best[0] - row[0] < 0.04]
            if len(exact_titles) == 1:
                best = exact_titles[0]
            elif best[0] - second[0] < 0.04 and best[3]['content'] != second[3]['content']:
                return None, f"후보 모호함: {best[3]['title']} / {second[3]['title']}"
    label = '완전 일치' if best[1] else f'운영 유사도 {best[0]:.1%}'
    return best[3], label


def content_for_board(entry, meta):
    """Keep authored strategy but show item examples from the destination board."""
    examples = '\n\n'.join(
        f"[{slot['name']}]\n· 저장된 아이템 예시: {' / '.join(slot['items'])}"
        for slot in board_data(meta) if slot['items'])
    if not examples:
        examples = '· 현재 저장된 배치에는 장착 아이템 예시가 없습니다.'
    return re.sub(r'(?ms)^챔피언 & 아이템\n\n.*?(?=^아이템 우선순위\n)',
                  lambda _: f'챔피언 & 아이템\n\n{examples}\n\n', entry['content'])


def read_guides(path):
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if payload.get('format') != FORMAT or not isinstance(payload.get('guides'), list):
            raise ValueError('지원하지 않는 설명 파일 형식입니다.')
        entries = payload['guides']
        seen = set()
        for entry in entries:
            title, content = entry['title'], entry['content']
            if (not isinstance(title, str) or not title.strip() or len(title) > 50
                    or not isinstance(content, str) or not content.strip()
                    or len(content) > 20000 or '\x00' in content):
                raise ValueError('제목 또는 설명이 올바르지 않습니다.')
            level = entry['default_level']
            if type(level) is not int or not 1 <= level <= 10:
                raise ValueError(f'{title}: 대표 레벨이 올바르지 않습니다.')
            if not isinstance(entry['board'], list) or not entry['board']:
                raise ValueError(f'{title}: 배치 정보가 비어 있습니다.')
            locations = set()
            for slot in entry['board']:
                if (not isinstance(slot['name'], str) or not slot['name'].strip()
                        or type(slot['star']) is not int or not 1 <= slot['star'] <= 3
                        or type(slot['location']) is not int or not 1 <= slot['location'] <= 28
                        or slot['location'] in locations
                        or not isinstance(slot['items'], list) or len(slot['items']) > 3
                        or any(not isinstance(item, str) or not item.strip()
                               for item in slot['items'])):
                    raise ValueError(f'{title}: 배치 정보가 올바르지 않습니다.')
                locations.add(slot['location'])
            identity = name_key(title)
            if identity in seen:
                raise ValueError(f'{title}: 중복된 제목입니다.')
            seen.add(identity)
        return entries
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise CommandError(f'설명 파일을 읽지 못했습니다: {exc}') from exc
