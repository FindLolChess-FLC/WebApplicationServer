from selenium import webdriver
from selenium.webdriver.common.by import By
from Meta.models import Augmenter, AugmenterImg

def augmenter_crawling():
    for tier in range(1,4):
        url = f'https://lolchess.gg/guide/augments/set13?tier={tier}'
        driver = webdriver.Chrome()

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
                if ':' in augment_instance.name:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/골드/{augment_instance.name.replace(':', '')}.png")
                else:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/골드/{augment_instance.name}.png")
            elif tier == 3:
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Platinum')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/프리즘/{augment_instance.name}.png")

    driver.quit()