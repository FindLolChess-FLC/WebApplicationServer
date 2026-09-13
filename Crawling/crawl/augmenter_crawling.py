"""Collect the visible season augments and their official image URLs."""
import html
import re
import tempfile
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


EXTRACT_SCRIPT = r"""
const root = JSON.parse(document.querySelector('#__NEXT_DATA__').textContent);
const candidates = [];
function walk(value) {
  if (Array.isArray(value)) {
    if (value.length && value.some(x => x && typeof x === 'object' &&
        'name' in x && 'desc' in x && 'imageUrl' in x && 'tier' in x)) {
      candidates.push(value);
    }
    value.forEach(walk);
  } else if (value && typeof value === 'object') {
    Object.values(value).forEach(walk);
  }
}
walk(root);
const source = candidates.sort((a, b) => b.length - a.length)[0] || [];
const shown = Array.from(document.querySelectorAll('section div[title]'))
  .map(node => ({name: node.getAttribute('title'),
                 img_src: node.parentElement.querySelector('img')?.getAttribute('src')}))
  .filter(x => x.name && x.img_src?.includes('/images/items/'));
return {source, shown};
"""

TIERS = {1: 'Silver', 2: 'Gold', 3: 'prism'}


def clean_description(value):
    value = re.sub(r'<br\s*/?>', ' ', value or '', flags=re.IGNORECASE)
    value = re.sub(r'<[^>]*>', ' ', value)
    return ' '.join(html.unescape(value).split())


def build_records(source, shown):
    """Keep only displayed entries, cross-checking image and name with page data."""
    if not source or not shown:
        raise ValueError('증강체 원본 데이터 또는 화면 목록이 비어 있습니다.')
    by_image = {}
    for row in source:
        if not row.get('isHidden'):
            by_image.setdefault(row.get('imageUrl'), []).append(row)

    records = []
    names = {}
    seen_cards = set()
    for card in shown:
        image = card['img_src']
        identity = (card['name'], image)
        if identity in seen_cards:
            continue
        seen_cards.add(identity)
        matches = [row for row in by_image.get(image, [])
                   if row.get('name', '').replace(' ', '') == card['name'].replace(' ', '')]
        if len(matches) != 1:
            raise ValueError(f'화면 증강체와 원본 데이터가 일치하지 않습니다: {card["name"]}')
        row = matches[0]
        name = ''.join(row['name'].split())
        effect = clean_description(row.get('desc'))
        parsed = urlparse(image)
        if not name or len(name) > 25:
            raise ValueError(f'잘못된 증강체 이름: {name}')
        if not effect or len(effect) > 500:
            raise ValueError(f'{name}: 설명이 없거나 DB 길이 500을 초과합니다 ({len(effect)}).')
        if parsed.scheme != 'https' or not parsed.netloc or len(image) > 255:
            raise ValueError(f'{name}: 잘못된 이미지 URL')
        tier = TIERS.get(row.get('tier'))
        if tier is None:
            raise ValueError(f'{name}: 알 수 없는 등급')
        if name in names:
            key = row.get('key') or ''
            suffix = '++' if key.endswith('PlusPlus') else '+' if key.endswith('Plus') else ''
            if suffix and not name.endswith(suffix):
                name += suffix
            if name in names:
                base = name
                index = 2
                while f'{base}({index})' in names:
                    index += 1
                name = f'{base}({index})'
            if len(name) > 25:
                raise ValueError(f'{name}: DB 이름 길이 25를 초과합니다.')
        names[name] = (tier, image)
        records.append({'name': name, 'effect': effect, 'tier': tier, 'img_src': image})
    if len(records) != len(seen_cards):
        raise ValueError('화면 증강체 일부가 누락됐습니다.')
    return records


def collect_augments(season=18, *, headless=True, timeout=30):
    if isinstance(season, bool) or not isinstance(season, int) or season < 1:
        raise ValueError('시즌은 양의 정수여야 합니다.')
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    with tempfile.TemporaryDirectory(prefix='flc-augment-chrome-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        driver = webdriver.Chrome(options=options)
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(f'https://lolchess.gg/augments/set{season}?type=all')
            WebDriverWait(driver, timeout).until(
                lambda current: current.find_elements(By.CSS_SELECTOR, 'section div[title]')
            )
            if not any(re.search(rf'시즌\s+{season}\s+증강체', h.text)
                       for h in driver.find_elements(By.TAG_NAME, 'h2')):
                raise ValueError(f'요청한 시즌{season} 페이지가 아닙니다: {driver.current_url}')
            data = driver.execute_script(EXTRACT_SCRIPT)
            return build_records(data['source'], data['shown'])
        finally:
            driver.quit()


def save_augments(records):
    from django.db import transaction
    from Meta.models import Augmenter, AugmenterImg

    with transaction.atomic():
        for record in records:
            augment, _ = Augmenter.objects.update_or_create(
                name=record['name'],
                defaults={'effect': record['effect'], 'tier': record['tier']},
            )
            AugmenterImg.objects.update_or_create(
                augmenter=augment, defaults={'img_src': record['img_src']},
            )


def augmenter_crawling(season=18, *, dry_run=False, headless=True):
    records = collect_augments(season, headless=headless)
    if not dry_run:
        save_augments(records)
    return records
