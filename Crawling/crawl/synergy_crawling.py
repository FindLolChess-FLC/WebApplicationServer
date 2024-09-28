from selenium import webdriver
from selenium.webdriver.common.by import By
from Meta.models import Synergy

# 시너지 정보 저장
def synergy_crawling():
    url = 'https://lolchess.gg/synergies/set12'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)

    synergy_name_data = driver.find_elements(By.CSS_SELECTOR, 'div > div.css-tb5sq7.edroetd8 > h6')
    synergy_effect_data = driver.find_elements(By.CLASS_NAME, 'css-1dk1fk9.edroetd4')

    for name,effect in zip(synergy_name_data, synergy_effect_data):
        Synergy.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text.replace('\n', ' '))

    driver.quit()