"""Collect LoLCHESS boards from the API used by its public frontend."""
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from Crawling.crawl.guide_text import guide_text


API_BASE_URL = 'https://tft.dakgg.io/api/v1'
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Origin': 'https://lolchess.gg',
    'Referer': 'https://lolchess.gg/meta?hl=ko',
}
_sessions = threading.local()


def fetch_lolchess_json(path, *, params=None, timeout=30):
    if not hasattr(_sessions, 'client'):
        client = requests.Session()
        client.headers.update(API_HEADERS)
        client.mount('https://', HTTPAdapter(max_retries=Retry(
            total=3, backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=('GET',), respect_retry_after_header=True)))
        _sessions.client = client
    response = _sessions.client.get(f'{API_BASE_URL}/{path.lstrip("/")}',
                                    params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_slots(slots, champions, items):
    result = []
    for slot in slots:
        champion = champions[slot['champion']]
        result.append({
            'name': champion['name'],
            'star': slot.get('star', 1),
            'location': slot['index'] + 1,
            'items': [items[key] for key in slot.get('items', [])],
            'is_summon': champion.get('isHidden', False)
                         and champion.get('cost', [None])[0] == 0,
            'image_url': champion['imageUrl'],
        })
    locations = [slot['location'] for slot in result]
    if (len(locations) != len(set(locations))
            or any(not 1 <= slot['location'] <= 28 or not 1 <= slot['star'] <= 3
                   for slot in result)):
        raise ValueError('lolchess.gg 배치 위치 또는 별 정보가 올바르지 않습니다.')
    return result


class _NextDataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_next_data = False
        self.data = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == '__NEXT_DATA__':
            self.in_next_data = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_next_data = False

    def handle_data(self, data):
        if self.in_next_data:
            self.data.append(data)


def _query_data(queries, key):
    for query in queries:
        if query.get('queryKey', [None])[0] == key:
            return query['state']['data']
    raise ValueError(f'lolchess.gg 응답에 {key} 데이터가 없습니다.')


def build_lolchess_records(champion_refs, item_refs, guide_data, season=18):
    expected_season = f'set{season}'
    if champion_refs['season'] != expected_season or item_refs['season'] != expected_season:
        raise ValueError(f'lolchess.gg 데이터가 {expected_season}이 아닙니다.')
    champions = {entry['key']: entry for entry in champion_refs['champions']}
    items = {entry['key']: entry['name'] for entry in item_refs['items']}
    records = []
    seen_ids = set()
    for guide in guide_data['guideDecks']:
        if guide.get('season') != expected_season or guide['data'].get('set') != expected_season:
            continue
        guide_id = guide['teamBuilderKey']
        if guide_id in seen_ids:
            raise ValueError(f'중복 가이드 ID: {guide_id}')
        seen_ids.add(guide_id)
        slots = build_slots(guide['data']['slots'], champions, items)
        if len(slots) < 5:
            continue
        records.append({
            'id': guide_id,
            'title': guide['name'].strip(),
            'season': season,
            'source_url': f'https://lolchess.gg/builder/guide/{guide_id}?type=guide&hl=ko',
            'champions': slots,
        })
    if not records:
        raise ValueError(f'lolchess.gg에서 {expected_season} 메타 덱을 찾지 못했습니다.')
    if len({record['title'] for record in records}) != len(records):
        raise ValueError('메타 덱 제목이 중복되어 DB 저장 시 구별할 수 없습니다.')
    return records


def parse_lolchess_meta(html, season=18):
    """Read previously captured server-rendered pages with the same board parser."""
    parser = _NextDataParser()
    parser.feed(html)
    if not parser.data:
        raise ValueError('lolchess.gg 응답에서 __NEXT_DATA__를 찾지 못했습니다.')
    queries = json.loads(''.join(parser.data))['props']['pageProps']['dehydratedState']['queries']
    return build_lolchess_records(_query_data(queries, 'championRefs'),
                                 _query_data(queries, 'itemRefs'),
                                 _query_data(queries, 'getGuideDecks'), season)


def collect_lolchess_meta(season=18, *, timeout=30, include_details=False, workers=5):
    params = {'hl': 'ko', 'season': f'set{season}'}
    champion_refs = fetch_lolchess_json('data/champions', params=params, timeout=timeout)
    item_refs = fetch_lolchess_json('data/items', params=params, timeout=timeout)
    guides = fetch_lolchess_json('guide-decks',
                                params={'q': 'live', 'hl': 'ko', 'newSet': 1},
                                timeout=timeout)
    records = build_lolchess_records(champion_refs, item_refs, guides, season)
    if include_details:
        attach_guides(records, champion_refs, item_refs, timeout=timeout, workers=workers)
    return records


def _board_key(slots):
    return sorted((slot['name'], slot['star'], slot['location'], tuple(sorted(slot['items'])))
                  for slot in slots)


def attach_guides(records, champion_refs, item_refs, *, timeout=30, workers=5):
    """Fetch each shared level board once, before callers change the database."""
    champions = {entry['key']: entry for entry in champion_refs['champions']}
    items = {entry['key']: entry['name'] for entry in item_refs['items']}
    lock = threading.Lock()
    last_request = 0.0

    def fetch(key):
        nonlocal last_request
        with lock:
            time.sleep(max(0, 0.5 - (time.monotonic() - last_request)))
            last_request = time.monotonic()
        return fetch_lolchess_json(f'team-builders/{key}',
                                  params={'hl': 'ko'}, timeout=timeout)['teamBuilder']

    with ThreadPoolExecutor(max_workers=workers) as pool:
        keys = list(dict.fromkeys(record['id'] for record in records))
        builders = dict(zip(keys, pool.map(fetch, keys)))
        level_keys = list(dict.fromkeys(
            key for builder in builders.values()
            for field, key in (builder.get('guide') or {}).items()
            if re.fullmatch(r'builder_lv(?:[1-9]|10)_uuid', field) and key
            and key not in builders))
        builders.update(zip(level_keys, pool.map(fetch, level_keys)))

    for record in records:
        builder = builders[record['id']]
        if (builder.get('name', '').strip() != record['title']
                or builder.get('season') != f'set{record["season"]}'):
            raise ValueError(f'{record["title"]}: 가이드 이름이나 시즌이 다릅니다.')
        guide = builder.get('guide') or {}
        contents = guide.get('contents') or []
        main = [part for part in contents if part.get('title', '').strip() == record['title']]
        if len(main) > 1:
            raise ValueError(f'{record["title"]}: 덱 설명 항목이 중복됩니다.')
        details = [{'level': 0, 'content': guide_text(main[0].get('content') or '')
                    if main else '', 'champions': []}]
        for field, key in guide.items():
            match = re.fullmatch(r'builder_lv([1-9]|10)_uuid', field)
            if not match or not key:
                continue
            level = int(match[1])
            board = builders[key]
            if board.get('season') != f'set{record["season"]}':
                raise ValueError(f'{record["title"]}: {level}레벨 배치 시즌이 다릅니다.')
            slots = build_slots(board.get('slots') or [], champions, items)
            if not slots:
                continue
            texts = [guide_text(part.get('content') or '') for part in contents
                     if re.fullmatch(rf'(?:lv\.?\s*{level}|{level}\s*레벨)',
                                     part.get('title', '').strip(), re.IGNORECASE)]
            details.append({'level': level, 'content': '\n\n'.join(filter(None, texts)),
                            'champions': slots})
        record['guides'] = details
        representative = _board_key(record['champions'])
        matched = [guide['level'] for guide in details
                   if guide['level'] and _board_key(guide['champions']) == representative]
        if matched:
            record['default_level'] = min(matched)
