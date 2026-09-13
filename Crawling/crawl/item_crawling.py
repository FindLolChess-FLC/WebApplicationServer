"""Collect season item data from lolchess.gg and optionally persist it."""
import json
import html
import re
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Crawling.crawl.browser import create_driver

from Crawling.utils import item_translation


ITEM_REFS_SCRIPT = r"""
const payload = document.querySelector('#__NEXT_DATA__');
if (!payload) return null;
const queries = JSON.parse(payload.textContent)
    .props?.pageProps?.dehydratedState?.queries || [];
return queries.find(query => query.queryKey?.[0] === 'itemRefs')?.state?.data || null;
"""


def _normalize_text(value):
    return ' '.join((value or '').split())


def _description(value):
    value = re.sub(r'<br\s*/?>', ' ', value or '', flags=re.IGNORECASE)
    value = re.sub(r'%i:[^%]+%', '', value)
    return _normalize_text(html.unescape(re.sub(r'<[^>]*>', ' ', value)))


def _source_card(name, image, refs, *, component=False):
    """Match a visible card to its same-season serialized item data."""
    matches = [row for row in refs['items']
               if (component or _normalize_text(row.get('name')) == _normalize_text(name))
               and unquote(row.get('imageUrl') or '') == unquote(image)]
    if not matches:
        same_name = [row for row in refs['items']
                     if _normalize_text(row.get('name')) == _normalize_text(name)]
        raise ValueError(f'{name}: 화면 이미지와 시즌 아이템 원본이 일치하지 않습니다. '
                         f'화면 URL={image!r}, 원본 URL='
                         f'{[row.get("imageUrl") for row in same_name[:3]]!r}')
    identities = {(_description(row.get('desc')),
                   tuple(row.get('compositions') or [])) for row in matches}
    if len(identities) == 1:
        effect, recipe_keys = identities.pop()
    else:
        # Some emblems have a second Augment reference with an extended
        # description. Keep the complete text only when both agree so far.
        effects = sorted((effect for effect, _ in identities), key=len)
        recipes = {recipe for _, recipe in identities}
        if len(recipes) == 1 and all(effects[-1].startswith(shorter)
                                     for shorter in effects[:-1]):
            effect, recipe_keys = effects[-1], recipes.pop()
        else:
            # Legacy game-mode variants can reuse the same portrait and name
            # with different stats. The unsuffixed key is the base item.
            base = min(matches, key=lambda row: len(row['key']))
            if not all(row['key'].startswith(base['key']) for row in matches):
                raise ValueError(f'{name}: 동일한 이미지에 서로 다른 아이템 데이터가 있습니다: '
                                 f'{[row.get("key") for row in matches]!r}')
            effect = _description(base.get('desc'))
            recipe_keys = tuple(base.get('compositions') or [])
    by_key = {row['key']: row for row in refs['items']}
    try:
        recipe = [by_key[key]['imageUrl'] for key in recipe_keys]
    except KeyError as exc:
        raise ValueError(f'{name}: 원본 데이터에 없는 조합 재료 키입니다.') from exc
    if component and recipe:
        raise ValueError(f'{name}: 기본 재료에 조합 재료가 설정됐습니다.')
    return {'name': name, 'effect': effect, 'img_src': image,
            'recipe_srcs': recipe}


def build_records(cards, components):
    """Validate item cards and resolve recipe image URLs to component names."""
    if not cards or not components:
        raise ValueError('아이템 목록 또는 기본 재료가 비어 있습니다.')

    component_by_src = {unquote(item['img_src']): _normalize_text(item['name'])
                        for item in components}
    if len(component_by_src) != 10:
        raise ValueError(f'기본 재료는 10개여야 합니다 ({len(component_by_src)}개).')

    records = []
    records_by_name = {}
    for raw in [*cards, *components]:
        name = _normalize_text(raw.get('name'))
        effect = _normalize_text(raw.get('effect'))
        image = raw.get('img_src') or ''
        recipe = raw.get('recipe_srcs') or []
        if not name or len(name) > 50:
            raise ValueError(f'잘못된 아이템 이름: {name}')
        if not effect or len(effect) > 500:
            raise ValueError(f'{name}: 설명이 없거나 DB 길이 500을 초과합니다 ({len(effect)}).')
        parsed = urlparse(image)
        if parsed.scheme != 'https' or not parsed.netloc or len(image) > 255:
            raise ValueError(f'{name}: 잘못된 이미지 URL')
        if len(recipe) not in (0, 2):
            raise ValueError(f'{name}: 조합 재료가 0개 또는 2개가 아닙니다.')
        try:
            materials = [component_by_src[unquote(src)] for src in recipe]
        except KeyError as exc:
            raise ValueError(f'{name}: 알 수 없는 조합 재료 이미지 URL') from exc

        record = {
            'name': name,
            'effect': effect,
            'item1': materials[0] if materials else '',
            'item2': materials[1] if materials else '',
            'img_src': image,
        }
        previous = records_by_name.get(name)
        if previous:
            if previous != record:
                same_identity = all(
                    previous[key] == record[key]
                    for key in ('name', 'item1', 'item2', 'img_src')
                )
                shorter, longer = sorted(
                    (previous['effect'], record['effect']), key=len
                )
                if same_identity and longer.startswith(shorter):
                    previous['effect'] = longer
                    continue
                differences = {
                    key: (previous[key], record[key])
                    for key in record
                    if previous[key] != record[key]
                }
                raise ValueError(
                    f'{name}: 중복된 항목의 내용이 서로 다릅니다: '
                    + json.dumps(differences, ensure_ascii=True)
                )
            continue
        records_by_name[name] = record
        records.append(record)
    return records


def collect_items(season=18, *, headless=True, timeout=30):
    if isinstance(season, bool) or not isinstance(season, int) or season < 1:
        raise ValueError('시즌은 양의 정수여야 합니다.')
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')

    with tempfile.TemporaryDirectory(prefix='flc-item-chrome-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        driver = create_driver(options, headless=headless)
        try:
            driver.set_page_load_timeout(timeout)
            base = f'https://lolchess.gg/items/set{season}'
            driver.get(base)
            cells = WebDriverWait(driver, timeout).until(
                lambda current: current.find_elements(By.CSS_SELECTOR, 'td.name')
            )
            _validate_season(driver, season)
            refs = WebDriverWait(driver, timeout).until(
                lambda current: current.execute_script(ITEM_REFS_SCRIPT)
            )
            if refs.get('season') != f'set{season}' or not refs.get('items'):
                raise ValueError(f'시즌{season} 아이템 원본 데이터가 아닙니다.')
            cards = []
            for index, cell in enumerate(cells, start=1):
                name = cell.find_element(
                    By.CSS_SELECTOR, '.content .name-row > span:first-child'
                ).text.strip()
                image = cell.find_element(By.CSS_SELECTOR, 'img.ItemPortrait')
                try:
                    cards.append(_source_card(name, image.get_attribute('src'), refs))
                except ValueError as exc:
                    raise ValueError(f'{index}/{len(cells)} {exc}') from exc

            driver.get(base + '/table')
            images = WebDriverWait(driver, timeout).until(
                lambda current: current.find_elements(
                    By.CSS_SELECTOR, 'table img[data-pos-y="0"][data-pos-x]'
                )
            )
            _validate_season(driver, season)
            components = []
            for index, image in enumerate(images, start=1):
                image_src = image.get_attribute('src')
                match = re.search(r'/items/([^_]+)_', image_src)
                expected_name = item_translation(match.group(1)) if match else None
                if not expected_name:
                    raise ValueError(f'알 수 없는 기본 재료 이미지 URL: {image_src}')
                try:
                    components.append(_source_card(expected_name, image_src,
                                                   refs, component=True))
                except ValueError as exc:
                    raise ValueError(f'{index}/{len(images)} {exc}') from exc
            return build_records(cards, components)
        finally:
            driver.quit()


def _validate_season(driver, season):
    headings = driver.find_elements(By.TAG_NAME, 'h2')
    if not any(re.search(rf'시즌\s+{season}\s+아이템', heading.text) for heading in headings):
        raise ValueError(f'요청한 시즌{season} 페이지가 아닙니다: {driver.current_url}')


def save_items(records):
    from django.db import transaction
    from Meta.models import Item, ItemImg

    with transaction.atomic():
        for record in records:
            item, _ = Item.objects.update_or_create(
                name=record['name'],
                defaults={
                    'effect': record['effect'],
                    'item1': record['item1'],
                    'item2': record['item2'],
                },
            )
            ItemImg.objects.update_or_create(
                item=item, defaults={'img_src': record['img_src']}
            )


def item_crawling(season=18, *, dry_run=False, headless=True):
    records = collect_items(season, headless=headless)
    if not dry_run:
        save_items(records)
    return records


def write_preview(records, path):
    Path(path).write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8'
    )
