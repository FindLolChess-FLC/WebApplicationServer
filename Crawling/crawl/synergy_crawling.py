from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from Meta.models import Synergy, SynergyImg

# 시너지 정보 저장
def synergy_crawling():
    url = 'https://lolchess.gg/synergies/set12'

    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(10)

    synergy_name_data = driver.find_elements(By.CSS_SELECTOR, 'div > div.css-tb5sq7.edroetd8 > h6')
    synergy_effect_data = driver.find_elements(By.CLASS_NAME, 'css-1dk1fk9.edroetd4')

    for name, effect in zip(synergy_name_data, synergy_effect_data):

        synergy_instance, created = Synergy.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text.replace('\n', ' '))
        SynergyImg.objects.get_or_create(synergy=synergy_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/시너지/{synergy_instance.name}.png")