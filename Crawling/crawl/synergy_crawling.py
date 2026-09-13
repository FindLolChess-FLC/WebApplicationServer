"""Collect synergy data independently of Django; persist only when requested."""
import re
import tempfile
import warnings
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

GUIDE_SCRIPT = r"""
function text(node) {
    if (node.nodeType === 3) return node.textContent;
    if (node.nodeType !== 1) return '';
    const tooltip = node.getAttribute('data-tooltip');
    if (tooltip) return ' ' + tooltip + ' ';
    if (node.tagName === 'IMG') return ' ' + (node.getAttribute('alt') || '') + ' ';
    if (node.tagName === 'BR') return ' ';
    return Array.from(node.childNodes).map(text).join('') +
        (['P', 'DIV'].includes(node.tagName) ? ' ' : '');
}
return Array.from(document.querySelectorAll('div.header > h4')).map(h => {
    const card = h.parentElement.parentElement;
    const desc = card.querySelector('.desc');
    const stats = card.querySelector('.stats');
    return {
        name: h.textContent,
        effect: desc && stats ? text(desc) + ' ' + text(stats) : null,
        img_src: h.parentElement.querySelector('img')?.getAttribute('src'),
    };
});
"""

STATS_SCRIPT = r"""
return Array.from(document.querySelectorAll('td.name'))
    .filter(cell => cell.querySelector('.trait-stat > .name'))
    .map(cell => ({
        label: cell.querySelector('.trait-stat > .name').textContent,
        tier: cell.querySelector('[style*="background"]')?.getAttribute('style')
            ?.match(/background\/(\w+)\.svg/)?.[1]
    }));
"""


def normalize_name(value):
    return re.sub(r'\s+', '', value or '')


def build_records(cards, rows):
    """Validate all data before allowing any writes; never truncate descriptions."""
    if not cards or not rows:
        raise ValueError('시너지 가이드 또는 통계가 비어 있습니다.')
    tiers = {}
    for row in rows:
        match = re.fullmatch(r'\s*(\d+)\s+(.+?)\s*', row['label'])
        tier = row.get('tier')
        if not match or tier not in {'bronze', 'silver', 'gold', 'chromatic', 'unique'}:
            raise ValueError(f'알 수 없는 시너지 통계 행: {row}')
        count, name = int(match[1]), normalize_name(match[2])
        if count < 1:
            raise ValueError('활성 인원은 양수여야 합니다.')
        levels = tiers.setdefault(name, {})
        tier = 'prism' if tier == 'chromatic' else tier
        if count in levels and levels[count] != tier:
            raise ValueError(f'{name}의 {count}인 등급이 서로 다릅니다.')
        levels[count] = tier
    guide_names = {normalize_name(card['name']) for card in cards}
    if set(tiers) - guide_names:
        raise ValueError(f'가이드에 없는 통계 시너지: {sorted(set(tiers) - guide_names)}')
    records, seen = [], set()
    for card in cards:
        name = normalize_name(card['name'])
        effect = ' '.join((card.get('effect') or '').split())
        image = card.get('img_src') or ''
        if not name or name in seen or len(name) > 15:
            raise ValueError(f'잘못되거나 중복된 시너지 이름: {name}')
        if not effect or len(effect) > 500:
            raise ValueError(f'{name}: 설명이 없거나 DB 길이 500을 초과합니다 ({len(effect)}).')
        if urlparse(image).scheme != 'https' or not urlparse(image).netloc or len(image) > 255:
            raise ValueError(f'{name}: 잘못된 이미지 URL')
        seen.add(name)
        levels = tiers.get(name, {})
        if not levels:
            warnings.warn(f'{name}: 통계 등급 없음; sequence=[]로 보존합니다.', stacklevel=2)
        records.append({
            'name': name, 'effect': effect, 'img_src': image,
            'sequence': [tier for _, tier in sorted(levels.items())],
        })
    return records


def collect_synergies(season=18, *, headless=True, timeout=30):
    if isinstance(season, bool) or not isinstance(season, int) or season < 1:
        raise ValueError('시즌은 양의 정수여야 합니다.')
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    with tempfile.TemporaryDirectory(prefix='flc-synergy-chrome-') as profile:
        # An isolated profile prevents conflicts with the user's open Chrome session.
        options.add_argument(f'--user-data-dir={profile}')
        driver = webdriver.Chrome(options=options)
        try:
            driver.set_page_load_timeout(timeout)
            base = f'https://lolchess.gg/synergies/set{season}'
            extracted = []
            for url, selector, script in (
                (base + '/guide', 'div.header > h4', GUIDE_SCRIPT),
                (base, 'td.name .trait-stat > .name', STATS_SCRIPT),
            ):
                driver.get(url)
                WebDriverWait(driver, timeout).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, selector)
                )
                headings = driver.find_elements(By.TAG_NAME, 'h2')
                if not any(re.search(rf'시즌\s+{season}\s+시너지', h.text) for h in headings):
                    raise ValueError(f'요청한 시즌{season} 페이지가 아닙니다: {driver.current_url}')
                extracted.append(driver.execute_script(script))
            return build_records(*extracted)
        finally:
            driver.quit()


def save_synergies(records):
    # Lazy imports keep collection / dry-run independent of database access.
    from django.db import transaction
    from Meta.models import Synergy, SynergyImg

    with transaction.atomic():
        for record in records:
            synergy, _ = Synergy.objects.update_or_create(
                name=record['name'],
                defaults={'effect': record['effect'], 'sequence': record['sequence']},
            )
            SynergyImg.objects.update_or_create(
                synergy=synergy, defaults={'img_src': record['img_src']},
            )


def synergy_crawling(season=18, *, dry_run=False, headless=True):
    records = collect_synergies(season, headless=headless)
    if not dry_run:
        save_synergies(records)
    return records
