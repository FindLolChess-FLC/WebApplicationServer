"""Collect OP.GG TFT comps from public cards or the legacy board layout."""
import json
import re
import tempfile
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Crawling.crawl.browser import create_driver


URL = 'https://op.gg/ko/tft/meta-trends/comps'
CARD_SELECTOR = 'ul.flex.flex-col.gap-1 > li'
FIREFOX_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)

BOARD_SCRIPT = r"""
const card = arguments[0];
const board = card.querySelector('div.flex.h-\\[192px\\]');
const grid = arguments[1]
    ? Array.from(card.querySelectorAll('div')).filter(element =>
        Array.from(element.children).filter(row => row.children.length === 7).length === 4).at(-1)
    : board?.querySelector(':scope > div > div');
if (!grid) return null;
const rows = Array.from(grid.children).filter(row => row.children.length === 7);
if (rows.length !== 4) return null;
const champions = [];
rows.forEach((row, rowIndex) => {
    Array.from(row.children).forEach((cell, columnIndex) => {
        const image = cell.querySelector('img[src*="/tft-champion/"]');
        if (!image) return;
        const stars = cell.querySelector('div.absolute.-top-1')?.querySelectorAll('svg').length || 1;
        champions.push({
            name: image.alt,
            location: rowIndex * 7 + columnIndex + 1,
            star: stars,
            items: Array.from(cell.querySelectorAll('img[src*="/tft-item/"]'), item => item.alt),
        });
    });
});
return {title: card.querySelector('strong')?.textContent.trim(), champions};
"""

SUMMARY_SCRIPT = r"""
const card = arguments[0];
const images = Array.from(card.querySelectorAll('img[src*="/tft-champion/"]'))
    .filter(image => !image.closest('div.flex.h-\\[192px\\]'));
return {
    title: card.querySelector('strong')?.textContent.trim(),
    champions: images.map(image => {
        const container = image.closest('div.relative.h-\\[32px\\]');
        return {name: image.alt, location: 0, star: 0,
            items: Array.from(container?.querySelectorAll('img[src*="/tft-item/"]') || [], item => item.alt)};
    }),
    complete: false,
};
"""


def validate_record(record, *, min_units=5):
    if not record or not record.get('title') or len(record['title']) > 50:
        raise ValueError(f'OP.GG 덱 제목이 비어 있거나 너무 깁니다: {record}')
    slots = record.get('champions') or []
    if not min_units <= len(slots) <= 28:
        raise ValueError(f'{record["title"]}: 챔피언 배치 {len(slots)}개')
    locations = set()
    for slot in slots:
        if (not slot.get('name') or len(slot['items']) > 3
                or any(not name for name in slot['items'])):
            raise ValueError(f'{record["title"]}: 잘못된 챔피언 배치 {slot}')
        if record.get('complete'):
            if (not 1 <= slot['location'] <= 28 or slot['location'] in locations
                    or not 1 <= slot['star'] <= 3):
                raise ValueError(f'{record["title"]}: 잘못된 챔피언 배치 {slot}')
            locations.add(slot['location'])
        elif slot['location'] != 0 or slot['star'] != 0:
            raise ValueError(f'{record["title"]}: 부분 수집에 실제 위치·별 값이 섞였습니다.')
    return record


class _CompSummaryParser(HTMLParser):
    """Read the public composition cards served before JavaScript runs."""

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.records = []
        self.card = None
        self.reading_title = False
        self.avatar = None
        self.avatar_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        slot = attrs.get('data-slot')
        if tag == 'article' and slot == 'tft-comp':
            self.card = {'id': attrs.get('data-comp-id'), 'title': '',
                         'champions': [], 'complete': False}
        if self.card is None:
            return
        href = attrs.get('href', '')
        if tag == 'a' and 'deckId=' in href and 'source_url' not in self.card:
            self.card['source_url'] = urljoin(self.url, href)
            self.reading_title = True
        if tag == 'div':
            if self.avatar is not None:
                self.avatar_depth += 1
            elif slot == 'tft-avatar':
                self.avatar = {'name': '', 'location': 0, 'star': 0, 'items': []}
                self.avatar_depth = 1
        if self.avatar is None:
            return
        if tag == 'span' and attrs.get('aria-label') and not self.avatar['name']:
            self.avatar['name'] = attrs['aria-label'].strip()
        if tag == 'img' and '/tft-item/' in attrs.get('src', ''):
            self.avatar['items'].append(attrs.get('alt', '').strip())

    def handle_data(self, data):
        if self.reading_title:
            self.card['title'] += data

    def handle_endtag(self, tag):
        if tag == 'a':
            self.reading_title = False
        if tag == 'div' and self.avatar is not None:
            self.avatar_depth -= 1
            if not self.avatar_depth:
                self.card['champions'].append(self.avatar)
                self.avatar = None
        if tag == 'article' and self.card is not None:
            self.card['title'] = self.card['title'].strip()
            self.records.append(validate_record(self.card))
            self.card = None


FLIGHT_PATTERN = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')


def read_deck_detail(html):
    """Return the selected deck's embedded detail data from the server-rendered page."""
    flight = ''.join(json.loads(f'"{chunk}"') for chunk in FLIGHT_PATTERN.findall(html))
    marker = flight.find('"initialDetail":')
    if marker < 0:
        raise ValueError('OP.GG 덱 상세 데이터를 찾지 못했습니다.')
    detail, _ = json.JSONDecoder().raw_decode(flight, flight.index('{', marker))
    return detail


def _resolve(detail, value):
    """Follow the page's `$id:...:initialDetail:path` references inside the same detail."""
    if not isinstance(value, str) or not value.startswith('$'):
        return value
    _, found, path = value.partition(':initialDetail:')
    if not found:
        raise ValueError(f'OP.GG 상세 참조를 해석할 수 없습니다: {value}')
    for key in path.split(':'):
        detail = detail[int(key)] if key.isdecimal() else detail[key]
    return detail


def apply_deck_detail(record, detail):
    """Fill a summary card with the deck's observed stars, items, displayed cells and levels."""
    data = detail['data']
    comp, guide = data['comp'], data['guide']
    if data['generation'].get('set') != 18 or comp['name'].strip() != record['title']:
        raise ValueError(f'{record["title"]}: 시즌 18 덱 상세 데이터가 아닙니다.')
    positioning = guide.get('positioning') or {}
    cells = {unit['unit']['name']: unit['cell'] for unit in positioning.get('units', [])
             if positioning.get('available') and isinstance(unit.get('cell'), int)}

    def slot(unit, items=()):
        return {'name': unit['name'], 'location': cells[unit['name']] + 1, 'star': unit['star'],
                'items': [_resolve(detail, item)['name'] for item in items]}

    try:
        champions = [slot(unit, unit['items']) for unit in comp['units']]
    except KeyError:
        return record
    guides = []
    for stage in (guide.get('timeline') or {}).get('levels', []):
        ranked = sorted(stage['units'], key=lambda row: row['appearanceRate'], reverse=True)
        units = [row['unit'] for row in ranked if row['unit']['cost'] > 0][:stage['level']]
        if len(units) == stage['level'] and all(unit['name'] in cells for unit in units):
            guides.append({'level': stage['level'], 'content': '', 'stars_observed': True,
                           'champions': [slot(unit) for unit in units]})
    return {**record, 'champions': champions, 'complete': True, 'stars_observed': True,
            'default_level': comp['level'], 'guides': guides}


def collect_deck_details(records, timeout):
    """Read each card's deck page in order; cards without displayed cells stay summaries."""
    detailed = []
    for record in records:
        if record.get('source_url'):
            response = requests.get(record['source_url'], timeout=timeout)
            response.raise_for_status()
            record = apply_deck_detail(record, read_deck_detail(response.text))
            for guide in record.get('guides', []):
                validate_record({'title': record['title'], 'complete': True,
                                 'champions': guide['champions']}, min_units=1)
        detailed.append(validate_record(record))
    return detailed


def collect_opgg_summaries(timeout):
    response = requests.get(URL, timeout=timeout)
    response.raise_for_status()
    parser = _CompSummaryParser(response.url)
    parser.feed(response.text)
    parser.close()
    if parser.records and not re.search(r'<title>[^<]*시즌 18\b', response.text):
        raise ValueError('OP.GG 시즌 18 페이지가 아닙니다.')
    return collect_deck_details(parser.records, timeout)


def collect_level_guides(driver, card, timeout):
    tabs = card.find_elements(By.XPATH, './/*[text()="초중반 배치표"]')
    if not tabs:
        return []
    driver.execute_script('arguments[0].scrollIntoView({block:"center"})', tabs[0])
    tabs[0].click()
    buttons = WebDriverWait(driver, timeout).until(lambda _: card.find_elements(
        By.XPATH, './/button[starts-with(normalize-space(.), "레벨 ")]'))
    levels = [int(match[1]) for button in buttons
              if (match := re.fullmatch(r'레벨\s+(\d+)', button.text.strip()))]
    guides = []
    for level in levels:
        button = card.find_element(By.XPATH, f'.//button[normalize-space(.)="레벨 {level}"]')
        driver.execute_script('arguments[0].scrollIntoView({block:"center"})', button)
        button.click()
        WebDriverWait(driver, timeout).until(lambda _: f'{level}레벨 빌드' in card.text)
        record = WebDriverWait(driver, timeout).until(
            lambda _: driver.execute_script(BOARD_SCRIPT, card, True))
        record['complete'] = True
        validate_record(record, min_units=1)
        guides.append({'level': level, 'content': '', 'champions': record['champions']})
    return guides


def collect_opgg_meta(*, headless=True, timeout=30, driver_factory=None):
    """Read current summary cards, with Selenium for the legacy layout."""
    if driver_factory is None:
        try:
            summaries = collect_opgg_summaries(timeout)
        except requests.RequestException:
            summaries = []
        if summaries:
            return summaries

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1440,900')
    options.add_argument('--lang=ko-KR')
    with tempfile.TemporaryDirectory(prefix='flc-opgg-chrome-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        driver = create_driver(options, headless=headless, driver_factory=driver_factory,
                               firefox_user_agent=FIREFOX_USER_AGENT)
        try:
            driver.set_page_load_timeout(timeout)
            agent = driver.execute_script('return navigator.userAgent')
            if headless and 'HeadlessChrome/' in agent:
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    'userAgent': agent.replace('HeadlessChrome/', 'Chrome/'),
                    'acceptLanguage': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                })
            driver.get(URL)
            try:
                WebDriverWait(driver, timeout).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, CARD_SELECTOR))
            except TimeoutException as exc:
                raise ValueError(f'OP.GG 덱 목록을 찾지 못했습니다: {driver.title} ({driver.current_url})') from exc
            if '시즌 18' not in driver.title:
                raise ValueError(f'OP.GG 시즌 18 페이지가 아닙니다: {driver.title}')
            count = len(driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR))
            records = []
            for index in range(count):
                card = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)[index]
                driver.execute_script('arguments[0].scrollIntoView({block:"center"})', card)
                card.find_element(By.CSS_SELECTOR, 'strong').click()
                try:
                    record = WebDriverWait(driver, min(timeout, 5)).until(
                        lambda d: (row if row and len(row['champions']) >= 5 else False)
                        if (row := d.execute_script(BOARD_SCRIPT, card)) is not None else False)
                    record['complete'] = True
                except TimeoutException:
                    record = driver.execute_script(SUMMARY_SCRIPT, card)
                links = card.find_elements(By.CSS_SELECTOR, 'a[href*="/meta-trends/comps/"]')
                if links:
                    record['source_url'] = links[0].get_attribute('href')
                    record['id'] = record['source_url'].split('/comps/', 1)[1].split('?', 1)[0]
                if record.get('complete'):
                    record['guides'] = collect_level_guides(driver, card, timeout)
                records.append(validate_record(record))
            return records
        finally:
            driver.quit()
