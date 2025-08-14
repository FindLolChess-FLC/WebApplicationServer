from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from Meta.models import Champion, Synergy, ChampionImg
from django.db import transaction
from Crawling.utils import get_img_src


# 챔피언 정보 저장
def champion_crawling():
    url = 'https://op.gg/ko/tft/meta-trends/champion'

    img_data = get_img_src('챔피언')

    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    driver.implicitly_wait(10)

    champ_name_data = driver.find_elements(By.CSS_SELECTOR,'tr.cursor-pointer > td:nth-child(2) > div > div:nth-child(2) > strong')
    champ_synergy_data = driver.find_elements(By.CSS_SELECTOR, 'tr.cursor-pointer > td:nth-child(2) > div > div:nth-child(2) > div')
    champ_price_data = driver.find_elements(By.CSS_SELECTOR,'tbody > tr > td:nth-child(3)')

    for name, synergy, price in zip(champ_name_data, champ_synergy_data, champ_price_data):
        with transaction.atomic():
            champion_instance, created = Champion.objects.get_or_create(name=name.text.replace(' ', ''), price=price.text[1])
            ChampionImg.objects.get_or_create(champion=champion_instance, img_src=img_data.get(champion_instance.name, 'empty'))
            synergy_names = [img.get_attribute("alt").strip().replace(' ', '') for img in synergy.find_elements(By.TAG_NAME, "img")]
            synergy_instances = list(Synergy.objects.filter(name__in=synergy_names))
            champion_instance.synergy.add(*synergy_instances)
        
    driver.quit()