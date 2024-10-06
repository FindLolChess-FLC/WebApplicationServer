from selenium import webdriver
from selenium.webdriver.common.by import By
from Meta.models import Augmenter, AugmenterImg
import requests
import os

def save_augment_img(tier, name, img):
    if tier == 1:
        save_directory = 'tft\증강\실버'
    elif tier == 2:
        save_directory = 'tft\증강\골드'
    elif tier == 3:
        save_directory = 'tft\증강\프리즘'
    file_path = os.path.join(save_directory, f"{name.text.replace(' ', '')}.png")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def augmenter_crawling():
    for tier in range(1,4):
        url = f'https://lolchess.gg/guide/augments/set12?tier={tier}'
        driver = webdriver.Chrome()

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > div > span')
        augment_effects = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > p')
        augment_img = driver.find_elements(By.CSS_SELECTOR, '.css-rbtdul.ept36rh2 > img')
        
        for name, effect, img in zip(augment_names, augment_effects, augment_img):
            # 증강체 변경사항이 있을때만 활성화
            # save_augment_img(tier, name, img.get_attribute('src'))
            if tier == 1 :
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Silver')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/v1728213857/tft/증강/실버/{augment_instance.name}.png")
            elif tier == 2:
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Gold')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/v1728213857/tft/증강/골드/{augment_instance.name}.png")
            elif tier == 3:
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Platinum')
                AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/v1728213857/tft/증강/프리즘/{augment_instance.name}.png")

    driver.quit()