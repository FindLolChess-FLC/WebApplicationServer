from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os

def save_augment_img(tier, name, img):
    if tier == 'silver':
        save_directory = 'tft\증강\실버'
    elif tier == 'gold':
        save_directory = 'tft\증강\골드'
    elif tier == 'prismatic':
        save_directory = 'tft\증강\프리즘'
    file_path = os.path.join(save_directory, f"{name.replace(' ', '')}.png")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_augment():
    tier_data = ['silver', 'gold', 'prismatic']
    for tier in tier_data:
        url = f'https://lolchess.gg/augments/set14?type={tier}'
        driver = webdriver.Chrome()

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-mbssy4.e110kr6610 > div > span')
        augment_img = driver.find_elements(By.CSS_SELECTOR, 'div.css-ok8zxw.e110kr669 > div > img')
        
        for name, img in zip(augment_names, augment_img):
            if ':' in name.text:
                save_augment_img(tier, name.text.replace(':',''), img.get_attribute('src'))
            else:
                save_augment_img(tier, name.text, img.get_attribute('src'))

    driver.quit()