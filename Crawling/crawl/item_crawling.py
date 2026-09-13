"""Collect season item data from lolchess.gg and optionally persist it."""
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Crawling.crawl.browser import create_driver

from Crawling.utils import item_translation


TOOLTIP_SCRIPT = r"""
const expected = arguments[0];
const strong = Array.from(document.querySelectorAll('body strong')).find(node =>
    node.getClientRects().length > 0 &&
    getComputedStyle(node).visibility !== 'hidden' &&
    node.textContent.replace(/\s+/g, '') === expected.replace(/\s+/g, '') &&
    Array.from(node.parentElement.children).some(child => child.tagName === 'P')
);
if (!strong) return null;
const root = strong.parentElement;
const result = {
    name: strong.textContent.trim(),
    effect: Array.from(root.children)
        .filter(child => child.tagName === 'P')
        .map(child => child.innerText.trim()).join(' '),
    recipe_srcs: Array.from(root.querySelectorAll('ul img'))
        .map(image => image.getAttribute('src')),
};
return result.effect ? result : null;
"""


def _normalize_text(value):
    return ' '.join((value or '').split())


def build_records(cards, components):
    """Validate item cards and resolve recipe image URLs to component names."""
    if not cards or not components:
        raise ValueError('아이템 목록 또는 기본 재료가 비어 있습니다.')

    component_by_src = {item['img_src']: _normalize_text(item['name']) for item in components}
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
            materials = [component_by_src[src] for src in recipe]
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


def _tooltip(driver, target, name, timeout):
    for attempt in range(3):
        if attempt:
            # Firefox occasionally drops a hover while scrolling a long grid.
            # Move off the card so a fresh mouseenter can fire on the retry.
            ActionChains(driver).move_to_element(
                driver.find_element(By.TAG_NAME, 'h2')).perform()
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
        ActionChains(driver).move_to_element(target).perform()
        if attempt == 2:
            # React tooltips also listen to mouseover; this handles a missed
            # native event in headless Firefox without changing the page.
            driver.execute_script(
                "arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles:true}));",
                target,
            )
        try:
            return WebDriverWait(driver, max(1, timeout / 3)).until(
                lambda current: current.execute_script(TOOLTIP_SCRIPT, name)
            )
        except TimeoutException:
            if attempt == 2:
                raise


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
            cards = []
            for index, cell in enumerate(cells, start=1):
                name = cell.find_element(
                    By.CSS_SELECTOR, '.content .name-row > span:first-child'
                ).text.strip()
                image = cell.find_element(By.CSS_SELECTOR, 'img.ItemPortrait')
                try:
                    data = _tooltip(driver, image, name, timeout)
                except Exception as exc:
                    raise RuntimeError(
                        f'{index}/{len(cells)} {name}: 아이템 설명 툴팁을 읽지 못했습니다.'
                    ) from exc
                data['img_src'] = image.get_attribute('src')
                cards.append(data)

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
                    data = _tooltip(driver, image, expected_name, timeout)
                except Exception as exc:
                    raise RuntimeError(
                        f'{index}/{len(images)}: 기본 재료 툴팁을 읽지 못했습니다.'
                    ) from exc
                data['recipe_srcs'] = []
                data['img_src'] = image_src
                components.append(data)
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
