from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from Meta.models import Champion, Synergy
from django.db import transaction

# 챔피언 정보 저장
def champion_crawling():
    url = 'https://tft.op.gg/meta-trends/champion'
    driver = webdriver.Chrome()

    driver.get(url)
    time.sleep(10)

    champ_name_data = driver.find_elements(By.CSS_SELECTOR,'div.css-19aklyh > div > table > tbody > tr > td.css-1gwaozl > a > div.champions-info > strong')
    champ_synergy_data = driver.find_elements(By.CSS_SELECTOR, 'div.css-19aklyh > div > table > tbody > tr > td.css-1gwaozl > a > div.champions-info > ul')
    champ_price_data = driver.find_elements(By.CSS_SELECTOR,'#__next > main > div > div.css-19aklyh > div > table > tbody > tr > td:nth-child(3)')

    for name, synergy, price in zip(champ_name_data, champ_synergy_data, champ_price_data):
        with transaction.atomic():
            champion_instance, created = Champion.objects.get_or_create(name=name.text.replace(' ', ''), price=price.text[1])
            synergy_instances = [synergy for synergy_name in (synergy.text).split('\n') for synergy in Synergy.objects.filter(name=synergy_name)]
            champion_instance.synergy.add(*synergy_instances)
        
    driver.quit()