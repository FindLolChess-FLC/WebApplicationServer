from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from Meta.models import Champion, Synergy, ChampionImg
from django.db import transaction
from Crawling.utils import get_img_src


# 챔피언 정보 저장
def champion_crawling():
    url = 'https://tft.op.gg/meta-trends/champion'
    img_data = get_img_src('챔피언')
    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(10)

    champ_name_data = driver.find_elements(By.CSS_SELECTOR,'div.css-19aklyh > div > table > tbody > tr > td.css-1gwaozl > a > div.champions-info > strong')
    champ_synergy_data = driver.find_elements(By.CSS_SELECTOR, 'div.css-19aklyh > div > table > tbody > tr > td.css-1gwaozl > a > div.champions-info > ul')
    champ_price_data = driver.find_elements(By.CSS_SELECTOR,'#__next > main > div > div.css-19aklyh > div > table > tbody > tr > td:nth-child(3)')

    for name, synergy, price in zip(champ_name_data, champ_synergy_data, champ_price_data):
        with transaction.atomic():
            champion_instance, created = Champion.objects.get_or_create(name=name.text.replace(' ', ''), price=price.text[1])
            ChampionImg.objects.get_or_create(champion=champion_instance, img_src=img_data.get(champion_instance.name, 'empty'))
            synergy_instances = [synergy for synergy_name in (synergy.text).split('\n') for synergy in Synergy.objects.filter(name=synergy_name.replace(' ',''))]
            champion_instance.synergy.add(*synergy_instances)
        
    driver.quit()