from selenium import webdriver
from selenium.webdriver.common.by import By
from Meta.models import Augmenter

def augmenter_crawling():
    for tier in range(1,4):
        url = f'https://lolchess.gg/guide/augments/set12?tier={tier}'
        driver = webdriver.Chrome()

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > div > span')
        augment_effects = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > p')

        for name, effect in zip(augment_names, augment_effects):
            if tier == 1 :
                Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Silver')
            elif tier == 2:
                Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Gold')
            elif tier == 3:
                Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Platinum')

    driver.quit()