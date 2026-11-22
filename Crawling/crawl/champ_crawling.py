"""Collect visible season champions and link them to saved synergies."""
import re
import tempfile
import warnings
from collections import Counter
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Crawling.crawl.browser import create_driver


EXTRACT_SCRIPT = r"""
const payload = document.querySelector('#__NEXT_DATA__');
if (!payload) return null;
const queries = JSON.parse(payload.textContent)
  .props?.pageProps?.dehydratedState?.queries || [];
const sources = queries.map(query => query.state?.data || {});
const championSource = sources.find(source => Array.isArray(source.champions));
const traitSource = sources.find(source => Array.isArray(source.traits));
const links = Array.from(document.querySelectorAll('a[href^="/champions/set"]'))
  .filter(link => link.querySelector('img[src*="/champions/"]'));
const shownImages = Array.from(new Map(links.map(link => [
  link.getAttribute('href'), link.querySelector('img').getAttribute('src')
])).values());
return {champions: championSource?.champions, traits: traitSource?.traits,
        seasons: [championSource?.season, traitSource?.season], shownImages};
"""


def normalize_name(value):
    return ''.join((value or '').split())


def build_records(champions, traits, shown_images):
    """Validate all public champions and their trait references before writing."""
    if not champions or not traits or not shown_images:
        raise ValueError('챔피언·시너지 데이터 또는 화면 목록이 비어 있습니다.')
    public = [champion for champion in champions if not champion.get('isHidden')]
    expected_images = Counter(champion.get('imageUrl') for champion in public)
    if expected_images != Counter(shown_images):
        raise ValueError('화면 챔피언 목록과 원본 공개 데이터가 일치하지 않습니다.')
    trait_names = {trait['key']: normalize_name(trait.get('name')) for trait in traits}
    records = []
    seen = set()
    for champion in public:
        name = normalize_name(champion.get('name'))
        cost = champion.get('cost')
        image = champion.get('imageUrl') or ''
        keys = champion.get('traits') or []
        if not name or name in seen or len(name) > 255:
            raise ValueError(f'잘못되거나 중복된 챔피언 이름: {name}')
        if not isinstance(cost, list) or not cost or isinstance(cost[0], bool) \
                or not isinstance(cost[0], int) or not 0 <= cost[0] <= 6:
            raise ValueError(f'{name}: 잘못된 1성 가격')
        parsed = urlparse(image)
        if parsed.scheme != 'https' or not parsed.netloc or len(image) > 255:
            raise ValueError(f'{name}: 잘못된 이미지 URL')
        if not keys or len(keys) != len(set(keys)) or any(key not in trait_names for key in keys):
            raise ValueError(f'{name}: 알 수 없거나 중복된 특성 키')
        names = [trait_names[key] for key in keys]
        if any(not value for value in names) or len(names) != len(set(names)):
            raise ValueError(f'{name}: 잘못된 특성 이름')
        seen.add(name)
        records.append({'name': name, 'price': cost[0], 'synergies': names,
                        'img_src': image})
    return records


def _extract_champion_page(driver, season, timeout):
    """Wait for source data; use it if Firefox cannot render the image cards."""
    def source_ready(current):
        result = current.execute_script(EXTRACT_SCRIPT)
        return result if result and result.get('champions') and result.get('traits') else False

    try:
        data = WebDriverWait(driver, timeout).until(source_ready)
    except TimeoutException as exc:
        raise ValueError(f'시즌{season} 챔피언 페이지 데이터를 기다렸지만 찾지 못했습니다: '
                         f'{driver.current_url}') from exc

    if data['seasons'] != [f'set{season}', f'set{season}']:
        raise ValueError(f'시즌{season} 챔피언·시너지 데이터가 아닙니다: {data["seasons"]}')

    expected = Counter(champion['imageUrl'] for champion in data['champions']
                       if not champion.get('isHidden'))
    if not expected or None in expected:
        raise ValueError('챔피언 원본 이미지 목록이 비어 있거나 잘못됐습니다.')

    def images_ready(current):
        result = current.execute_script(EXTRACT_SCRIPT)
        return result if result and Counter(result.get('shownImages') or []) == expected else False

    try:
        rendered = WebDriverWait(driver, min(timeout, 10)).until(images_ready)
        if rendered['seasons'] != data['seasons']:
            raise ValueError('챔피언 화면 렌더링 중 시즌 데이터가 변경됐습니다.')
        return build_records(rendered['champions'], rendered['traits'],
                             rendered['shownImages'])
    except TimeoutException:
        # The official page embeds the complete season data in __NEXT_DATA__.
        # Headless Firefox can leave the client-rendered card grid empty.
        latest = driver.execute_script(EXTRACT_SCRIPT)
        if latest and latest.get('shownImages'):
            raise ValueError('챔피언 화면 목록과 원본 공개 데이터가 일치하지 않습니다: '
                             f'{len(latest["shownImages"])} / {sum(expected.values())}개')
        warnings.warn('챔피언 화면 목록이 렌더링되지 않아 시즌 원본 데이터로 수집합니다.',
                      stacklevel=2)
        return build_records(data['champions'], data['traits'],
                             list(expected.elements()))


def collect_champions(season=18, *, headless=True, timeout=30):
    if isinstance(season, bool) or not isinstance(season, int) or season < 1:
        raise ValueError('시즌은 양의 정수여야 합니다.')
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    with tempfile.TemporaryDirectory(prefix='flc-champion-chrome-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        driver = create_driver(options, headless=headless)
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(f'https://lolchess.gg/champions/set{season}')
            if not any(re.search(rf'시즌\s+{season}\s+챔피언', heading.text)
                       for heading in driver.find_elements(By.TAG_NAME, 'h2')):
                raise ValueError(f'요청한 시즌{season} 페이지가 아닙니다: {driver.current_url}')
            return _extract_champion_page(driver, season, timeout)
        finally:
            driver.quit()


def save_champions(records):
    from django.db import transaction
    from Meta.models import Champion, ChampionImg, Synergy

    all_names = {name for record in records for name in record['synergies']}
    synergies = {synergy.name: synergy for synergy in Synergy.objects.filter(name__in=all_names)}
    missing = all_names - synergies.keys()
    if missing:
        raise ValueError(f'DB에 없는 시너지: {sorted(missing)}')

    with transaction.atomic():
        for record in records:
            champion, _ = Champion.objects.update_or_create(
                name=record['name'], defaults={'price': record['price']}
            )
            champion.synergy.set([synergies[name] for name in record['synergies']])
            ChampionImg.objects.update_or_create(
                champion=champion, defaults={'img_src': record['img_src']}
            )


def champion_crawling(season=18, *, dry_run=False, headless=True):
    records = collect_champions(season, headless=headless)
    if not dry_run:
        save_champions(records)
    return records
