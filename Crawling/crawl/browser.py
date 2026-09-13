"""Start Selenium in headless Linux deployments with Chrome or Firefox."""
import os
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


def _firefox_only_linux():
    if os.name != 'posix' or os.environ.get('CHROME_BIN') or os.environ.get('CHROMEDRIVER_PATH'):
        return False
    if any(shutil.which(name) for name in ('chromium', 'chromium-browser',
                                           'google-chrome', 'google-chrome-stable')):
        return False
    return bool(os.environ.get('FIREFOX_BIN') or shutil.which('firefox')
                or Path('/usr/bin/firefox').is_file())


def create_driver(chrome_options, *, headless=True, driver_factory=None):
    if driver_factory is not None:
        return driver_factory(options=chrome_options)

    if _firefox_only_linux():
        options = FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--width=1440')
        options.add_argument('--height=900')
        options.set_preference('intl.accept_languages', 'ko-KR,ko')
        if os.environ.get('FIREFOX_BIN'):
            options.binary_location = os.environ['FIREFOX_BIN']
        geckodriver = (os.environ.get('GECKODRIVER_PATH') or shutil.which('geckodriver'))
        if not geckodriver and Path('/usr/local/bin/geckodriver').is_file():
            geckodriver = '/usr/local/bin/geckodriver'
        service = FirefoxService(executable_path=geckodriver) if geckodriver else None
        return webdriver.Firefox(options=options, service=service)

    if os.environ.get('CHROME_BIN'):
        chrome_options.binary_location = os.environ['CHROME_BIN']
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        chrome_options.add_argument('--no-sandbox')
    chromedriver = os.environ.get('CHROMEDRIVER_PATH')
    if chromedriver:
        return webdriver.Chrome(options=chrome_options,
                                service=ChromeService(executable_path=chromedriver))
    return webdriver.Chrome(options=chrome_options)
