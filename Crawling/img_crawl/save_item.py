from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os
import re

def item_translation(data):
    if data == 'BFSword':
        return 'B.F.대검'
    elif data == 'RecurveBow':
        return '곡궁'
    elif data == 'ChainVest':
        return '쇠사슬 조끼'
    elif data == 'NegatronCloak':
        return '음전자 망토'
    elif data == 'NeedlesslyLargeRod':
        return '쓸데없이 큰 지팡이'
    elif data == 'Tearofthegoddess':
        return '여신의 눈물'
    elif data == 'GiantsBelt':
        return '거인의 허리띠'
    elif data == 'SparringGloves':
        return '연습용 장갑'
    elif data == 'Spatula':
        return '뒤집개'
    elif data == 'FryingPan':
        return '프라이팬'

def save_item_img(name, img):
    save_directory = 'tft\아이템'
    file_path = os.path.join(save_directory, f"{name.text.replace(' ', '')}.png") if type(name) != str else os.path.join(save_directory, f"{name.replace(' ', '')}.png")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_item():
    url = 'https://lolchess.gg/meta/items?type=all'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)

    item_data = driver.find_elements(By.CSS_SELECTOR,'tr > td.item')

    for item in item_data:
        name = item.find_element(By.CSS_SELECTOR, 'div > div:nth-child(2) > span')
        img = item.find_element(By.CSS_SELECTOR, 'div > div.relative.overflow-hidden > img').get_attribute('src')
        save_item_img(name, img)
    
    comb_url = 'https://lolchess.gg/items/set12'
    driver.get(comb_url)
    driver.implicitly_wait(10)
    
    comb_item_data = driver.find_elements(By.CSS_SELECTOR, 'button > div > img')

    for comb_item in comb_item_data:
        name = item_translation(re.findall(r'(?:items|item)/([^/_.]+)', comb_item.get_attribute('src'))[0])
        img = comb_item.get_attribute('src')
        save_item_img(name, img)

    driver.quit()
