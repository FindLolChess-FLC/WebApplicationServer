"""Collect LoLCHESS.GG recommended comps from the server-rendered meta page."""
import json
import tempfile
from html.parser import HTMLParser

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from Crawling.crawl.browser import create_driver


META_URL = 'https://lolchess.gg/meta?hl=ko'
BROWSER_USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
)
REQUEST_HEADERS = {
    'User-Agent': BROWSER_USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
              'image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://lolchess.gg/',
}


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


def fetch_lolchess_html(url, *, timeout=30, driver_factory=None):
    """Fetch normally, then use the deployment browser when the server gets 403."""
    response = requests.get(url, timeout=timeout, headers=REQUEST_HEADERS)
    if response.status_code != 403:
        response.raise_for_status()
        return response.text

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1440,900')
    options.add_argument('--lang=ko-KR')
    with tempfile.TemporaryDirectory(prefix='flc-lolchess-browser-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        driver = create_driver(
            options, driver_factory=driver_factory,
            firefox_user_agent=BROWSER_USER_AGENT,
        )
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            try:
                html = WebDriverWait(driver, timeout).until(
                    lambda browser: browser.page_source
                    if '__NEXT_DATA__' in browser.page_source else False)
            except TimeoutException as exc:
                raise ValueError(
                    f'lolchess.gg 브라우저 응답에서 데이터를 찾지 못했습니다: '
                    f'{driver.title} ({driver.current_url})'
                ) from exc
            return html
        finally:
            driver.quit()


def _query_data(queries, key):
    for query in queries:
        if query.get('queryKey', [None])[0] == key:
            return query['state']['data']
    raise ValueError(f'lolchess.gg 응답에 {key} 데이터가 없습니다.')


def parse_lolchess_meta(html, season=18):
    parser = _NextDataParser()
    parser.feed(html)
    if not parser.data:
        raise ValueError('lolchess.gg 응답에서 __NEXT_DATA__를 찾지 못했습니다.')
    queries = json.loads(''.join(parser.data))['props']['pageProps']['dehydratedState']['queries']
    champion_refs = _query_data(queries, 'championRefs')
    item_refs = _query_data(queries, 'itemRefs')
    guide_data = _query_data(queries, 'getGuideDecks')
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
        slots = []
        for slot in guide['data']['slots']:
            if slot['champion'] not in champions:
                raise ValueError(f"알 수 없는 챔피언: {slot['champion']}")
            unknown_items = set(slot.get('items', [])) - items.keys()
            if unknown_items:
                raise ValueError(f'알 수 없는 아이템: {sorted(unknown_items)}')
            slots.append({
                'name': champions[slot['champion']]['name'],
                'star': slot.get('star', 1),
                'location': slot['index'] + 1,
                'items': [items[key] for key in slot.get('items', [])],
                'is_summon': champions[slot['champion']].get('isHidden', False)
                             and champions[slot['champion']].get('cost', [None])[0] == 0,
                'image_url': champions[slot['champion']]['imageUrl'],
            })
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


def collect_lolchess_meta(season=18, *, timeout=30, driver_factory=None):
    html = fetch_lolchess_html(
        META_URL, timeout=timeout, driver_factory=driver_factory)
    return parse_lolchess_meta(html, season=season)


def lolchess_crawling():
    """Legacy shape used by the existing multi-source meta command."""
    return {
        record['title']: {
            '챔프': [slot['name'] for slot in record['champions']],
            '별': {slot['name']: slot['star'] for slot in record['champions']},
            '위치': {slot['name']: slot['location'] for slot in record['champions']},
            '아이템': {slot['name']: slot['items'] for slot in record['champions']},
        }
        for record in collect_lolchess_meta()
    }
