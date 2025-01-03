from selenium import webdriver
from selenium.webdriver.common.by import By
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

def save_augment():
    for tier in range(1,4):
        url = f'https://lolchess.gg/guide/augments/set12?tier={tier}'
        driver = webdriver.Chrome()

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-255197.ept36rh4 > div > div > div > div > span')
        augment_img = driver.find_elements(By.CSS_SELECTOR, '.css-rbtdul.ept36rh2 > img')
        
        for name, img in zip(augment_names, augment_img):
            save_augment_img(tier, name, img.get_attribute('src'))

    driver.quit()