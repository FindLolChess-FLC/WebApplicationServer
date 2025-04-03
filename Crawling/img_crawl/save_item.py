from selenium import webdriver
from selenium.webdriver.common.by import By

from Crawling.utils import item_translation

import requests
import os
import re

def save_item_img(name, img):
    save_directory = 'tft\아이템'
    file_path = os.path.join(save_directory, f"{name.text.replace(' ', '')}.png") if type(name) != str else os.path.join(save_directory, f"{name.replace(' ', '')}.png")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_item():
    url = 'https://lolchess.gg/items/set14'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)

    item_data = driver.find_elements(By.CSS_SELECTOR,'tr > td.name')

    for item in item_data:
        name = item.find_element(By.CSS_SELECTOR, 'div > div:nth-child(2) > span')
        img = item.find_element(By.CSS_SELECTOR, 'div > div.relative.overflow-hidden > img').get_attribute('src')
        save_item_img(name, img)
    
    comb_url = 'https://lolchess.gg/items/set14/table'
    driver.get(comb_url)
    driver.implicitly_wait(10)
    
    comb_item_data = driver.find_elements(By.CSS_SELECTOR, 'tr:nth-child(1) > td > div > div > div > div > img')

    for comb_item in comb_item_data:
        name = item_translation(re.findall(r'TFT_Item_([^\.]+)\.png', comb_item.get_attribute('src'))[0])
        print(name)
        img = comb_item.get_attribute('src')
        save_item_img(name, img)

    driver.quit()
