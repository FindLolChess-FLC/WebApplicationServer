from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from Meta.models import Augmenter, AugmenterImg

def augmenter_crawling():
    for tier in range(1,4):
        url = f'https://lolchess.gg/guide/augments/set12?tier={tier}'
        
        service = Service('/usr/local/bin/geckodriver')
        options = Options()
        options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
        options.add_argument("--headless")
        options.binary_location = '/usr/bin/firefox'
        driver = webdriver.Firefox(service=service, options=options)

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > div > span')
        augment_effects = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > p')
        
        for name, effect in zip(augment_names, augment_effects):
            if tier == 1 :
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Silver')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/실버/{augment_instance.name}.png")
            elif tier == 2:
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Gold')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/골드/{augment_instance.name}.png")
            elif tier == 3:
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Platinum')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/프리즘/{augment_instance.name}.png")

    driver.quit()