"""Use the deployment server's original headless Firefox setup on Linux."""
import os
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


def _is_linux():
    return sys.platform.startswith('linux')


def create_driver(chrome_options, *, headless=True, driver_factory=None,
                  firefox_user_agent=None):
    if driver_factory is not None:
        return driver_factory(options=chrome_options)

    if _is_linux():
        firefox_binary = os.environ.get('FIREFOX_BIN', '/usr/bin/firefox')
        geckodriver = os.environ.get('GECKODRIVER_PATH', '/usr/local/bin/geckodriver')
        if not Path(firefox_binary).is_file() or not Path(geckodriver).is_file():
            raise RuntimeError(
                'Linux 크롤링에는 Firefox와 GeckoDriver가 필요합니다. '
                f'확인할 경로: {firefox_binary}, {geckodriver}. '
                '필요하면 FIREFOX_BIN, GECKODRIVER_PATH를 지정하세요.'
            )

        options = FirefoxOptions()
        options.set_preference('intl.accept_languages', 'ko,ko-KR,ko-kr')
        if headless:
            options.add_argument('--headless')
        options.binary_location = firefox_binary
        if firefox_user_agent:
            options.set_preference('general.useragent.override', firefox_user_agent)
        driver = webdriver.Firefox(
            service=FirefoxService(geckodriver), options=options,
        )
        driver.set_window_size(1440, 900)
        return driver

    return webdriver.Chrome(options=chrome_options)
