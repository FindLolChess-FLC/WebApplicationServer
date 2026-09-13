"""Collect current tactics.tools team-composition summaries with Selenium."""
import os
import tempfile

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


URL = 'https://tactics.tools/ko/team-compositions'
CARD_SELECTOR = '.tc-summary-wrap'
CARD_SCRIPT = r"""
return Array.from(document.querySelectorAll('.tc-summary-wrap')).map(card => {
    const images = Array.from(card.querySelectorAll('img[alt]'))
        .filter(image => image.parentElement.className.includes('mx-[3px]'));
    return {
        title: card.querySelector('.text-lg.pl-1')?.textContent.trim(),
        champions: images.map(image => ({
            name: image.alt,
            star: 0,
            location: 0,
            items: Array.from(image.parentElement.querySelectorAll('img[alt]'))
                .filter(item => item !== image).map(item => item.alt),
        })),
        complete: false,
    };
});
"""


def validate_tactics_records(records):
    if not records:
        raise ValueError('tactics.tools 덱 목록이 비어 있습니다.')
    titles = set()
    for record in records:
        title = record.get('title') or ''
        slots = record.get('champions') or []
        if not title or len(title) > 50 or title in titles:
            raise ValueError(f'tactics.tools 덱 제목이 잘못되었거나 중복됩니다: {title}')
        if not 5 <= len(slots) <= 28 or any(not slot.get('name') for slot in slots):
            raise ValueError(f'{title}: 챔피언 목록이 비어 있거나 잘못되었습니다.')
        if any(slot['location'] != 0 or slot['star'] != 0 for slot in slots):
            raise ValueError(f'{title}: 출처에 없는 배치·별 정보를 추정하면 안 됩니다.')
        titles.add(title)
    return records


def collect_tactics_meta(*, timeout=30, driver_factory=None):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1440,900')
    options.add_argument('--lang=ko-KR')
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        options.add_argument('--no-sandbox')
    if os.environ.get('CHROME_BIN'):
        options.binary_location = os.environ['CHROME_BIN']
    with tempfile.TemporaryDirectory(prefix='flc-tactics-chrome-') as profile:
        options.add_argument(f'--user-data-dir={profile}')
        if driver_factory:
            driver = driver_factory(options=options)
        else:
            service_path = os.environ.get('CHROMEDRIVER_PATH')
            driver = webdriver.Chrome(
                options=options,
                service=Service(executable_path=service_path) if service_path else None,
            )
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(URL)
            try:
                WebDriverWait(driver, timeout).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, CARD_SELECTOR))
            except TimeoutException as exc:
                raise ValueError(f'tactics.tools 덱 목록을 찾지 못했습니다: {driver.title}') from exc
            # Cards are appended as the bottom of the page enters the viewport.
            stable_scrolls = 0
            for _ in range(10):
                before = len(driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR))
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                try:
                    WebDriverWait(driver, 2).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)) > before)
                except TimeoutException:
                    stable_scrolls += 1
                    if stable_scrolls >= 2:
                        break
                else:
                    stable_scrolls = 0
            return validate_tactics_records(driver.execute_script(CARD_SCRIPT))
        finally:
            driver.quit()


def tactics_crawling():
    """Existing meta-data shape; zero means location/star was not provided."""
    return {
        record['title']: {
            '챔프': [slot['name'] for slot in record['champions']],
            '별': {slot['name']: slot['star'] for slot in record['champions']},
            '위치': {slot['name']: slot['location'] for slot in record['champions']},
            '아이템': {slot['name']: slot['items'] for slot in record['champions']},
        }
        for record in collect_tactics_meta()
    }
