"""Start Selenium in headless Linux deployments with Chrome or Firefox."""
import os
import platform
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


def _driver_path(variable, *names):
    configured = os.environ.get(variable)
    if configured:
        return configured
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _firefox_driver_path():
    path = _driver_path('GECKODRIVER_PATH', 'geckodriver')
    if not path and Path('/usr/local/bin/geckodriver').is_file():
        path = '/usr/local/bin/geckodriver'
    return path


def _firefox_only_linux(chromedriver):
    if os.name != 'posix' or chromedriver or os.environ.get('CHROME_BIN'):
        return False
    firefox = (os.environ.get('FIREFOX_BIN') or shutil.which('firefox')
               or Path('/usr/bin/firefox').is_file())
    return bool(firefox and _firefox_driver_path())


def _needs_explicit_driver():
    return os.name == 'posix' and platform.machine().lower() in ('aarch64', 'arm64')


def create_driver(chrome_options, *, headless=True, driver_factory=None):
    if driver_factory is not None:
        return driver_factory(options=chrome_options)

    chromedriver = _driver_path('CHROMEDRIVER_PATH', 'chromedriver',
                                'chromium.chromedriver')
    if _firefox_only_linux(chromedriver):
        options = FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--width=1440')
        options.add_argument('--height=900')
        options.set_preference('intl.accept_languages', 'ko-KR,ko')
        if os.environ.get('FIREFOX_BIN'):
            options.binary_location = os.environ['FIREFOX_BIN']
        return webdriver.Firefox(
            options=options, service=FirefoxService(executable_path=_firefox_driver_path()),
        )

    if _needs_explicit_driver() and not chromedriver:
        raise RuntimeError(
            'Linux ARM64에서는 현재 Selenium Manager가 드라이버를 찾을 수 없습니다. '
            'Chromium/ChromeDriver 또는 Firefox/GeckoDriver를 설치하고 '
            'CHROMEDRIVER_PATH 또는 GECKODRIVER_PATH를 지정하세요.'
        )

    chrome_binary = _driver_path('CHROME_BIN', 'chromium', 'chromium-browser',
                                 'google-chrome', 'google-chrome-stable')
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        chrome_options.add_argument('--no-sandbox')
    if chromedriver:
        return webdriver.Chrome(options=chrome_options,
                                service=ChromeService(executable_path=chromedriver))
    return webdriver.Chrome(options=chrome_options)
