"""Collect OP.GG TFT comps with headless Chrome, including board positions."""
import tempfile

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Crawling.crawl.browser import create_driver


URL = 'https://op.gg/ko/tft/meta-trends/comps'
CARD_SELECTOR = 'ul.flex.flex-col.gap-1 > li'

BOARD_SCRIPT = r"""
const card = arguments[0];
const board = card.querySelector('div.flex.h-\\[192px\\]');
const grid = board?.querySelector(':scope > div > div');
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


def validate_record(record):
    if not record or not record.get('title') or len(record['title']) > 50:
        raise ValueError(f'OP.GG 덱 제목이 비어 있거나 너무 깁니다: {record}')
    slots = record.get('champions') or []
    if not 5 <= len(slots) <= 28:
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


def collect_opgg_meta(*, headless=True, timeout=30, driver_factory=None):
    """Read the exact OP.GG comps URL in a headless browser.

    CloudFront currently rejects Chrome's ``HeadlessChrome`` user agent. CDP
    changes that token before navigation, retaining the installed Chrome
    version and platform. Linux can also use its existing Firefox/GeckoDriver.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1440,900')
    options.add_argument('--lang=ko-KR')
    with tempfile.TemporaryDirectory(prefix='flc-opgg-chrome-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        driver = create_driver(options, headless=headless, driver_factory=driver_factory)
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
                records.append(validate_record(record))
            return records
        finally:
            driver.quit()


def opgg_crawling():
    """Legacy shape used by the older three-site management command."""
    result = {}
    for record in collect_opgg_meta():
        if not record['complete']:
            continue
        result[record['title']] = {
            '챔프': [slot['name'] for slot in record['champions']],
            '별': {slot['name']: slot['star'] for slot in record['champions']},
            '위치': {slot['name']: slot['location'] for slot in record['champions']},
            '아이템': {slot['name']: slot['items'] for slot in record['champions']},
        }
    return result
