from selenium import webdriver
from selenium.webdriver.common.by import By
from Meta.models import Augmenter, AugmenterImg

def augmenter_crawling():
    tier_data = ['silver', 'gold', 'prismatic']
    for tier in tier_data:
        url = f'https://lolchess.gg/augments/set13?type={tier}'
        driver = webdriver.Chrome()

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-mbssy4.e110kr668 > div > span')
        augment_effects = driver.find_elements(By.CLASS_NAME, 'css-uh2eun.e110kr6612')
        
        for name, effect in zip(augment_names, augment_effects):
            if tier == 'silver' :
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text.replace('\n', ''), tier='Silver')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/실버/{augment_instance.name}.png")
            elif tier == 'gold':
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Gold')
                if ':' in augment_instance.name:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/골드/{augment_instance.name.replace(':', '')}.png")
                else:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/골드/{augment_instance.name}.png")
            elif tier == 'prismatic':
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='prism')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/증강/프리즘/{augment_instance.name}.png")

    driver.quit()