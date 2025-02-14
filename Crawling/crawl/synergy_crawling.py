from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from Meta.models import Synergy, SynergyImg
from Crawling.utils import get_img_src
import re


# 시너지 정보 저장
def synergy_crawling():
    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    driver = webdriver.Firefox(service=service, options=options)

    synergy_type = ['bronze', 'silver', 'gold', 'chromatic']
    synergy_type_data = {}

    img_data = get_img_src('시너지')

    for type in synergy_type:
        url = f'https://lolchess.gg/synergies/set13?type={type}'

        driver.get(url)
        driver.implicitly_wait(10)
        name_data = driver.find_elements(By.CSS_SELECTOR, 'div.trait-stat> .name')

        for data in name_data:
            name = re.sub(r'\d+', '', data.text).strip().replace(' ', '')

            if name in synergy_type_data:
                synergy_type_data[name].append(type if type != 'chromatic' else 'prism')
            elif (type == 'gold') & (data.text.split(' ')[0] == '1'):
                synergy_type_data[name] = ['unique']
            else:
                synergy_type_data[name] = []
                synergy_type_data[name].append(type if type != 'chromatic' else 'prism')

    url = 'https://lolchess.gg/synergies/set13/guide'
    driver.get(url)
    driver.implicitly_wait(10)

    synergy_name_data = driver.find_elements(By.CSS_SELECTOR, ' div.header > h4')
    synergy_desc_data = driver.find_elements(By.CLASS_NAME, 'desc')
    synergy_effect_data = driver.find_elements(By.CLASS_NAME, 'stats')

    for name, effect, desc in zip(synergy_name_data, synergy_effect_data, synergy_desc_data):
        sequence_data = synergy_type_data.get(name.text.replace(' ', ''))
        synergy_instance, created = Synergy.objects.get_or_create(name=name.text.replace(' ', ''), 
                                                                effect=desc.text.replace('\n', ' ') + effect.text.replace('\n', ' '), 
                                                                sequence=(sequence_data if sequence_data else [])
)
        SynergyImg.objects.get_or_create(synergy=synergy_instance, img_src=img_data[synergy_instance.name])
