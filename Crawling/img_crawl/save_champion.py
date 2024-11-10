from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os

def save_champion_img(name, img):
    save_directory = 'tft\챔피언'
    file_path = os.path.join(save_directory, f"{name.text.replace(' ', '')}.png") if name != '노라' else os.path.join(save_directory, f"노라.png")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_champion():
    url = 'https://tft.op.gg/meta-trends/champion'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)

    champ_data = driver.find_elements(By.CSS_SELECTOR,'td.css-1gwaozl')

    for champ in champ_data:
        name = champ.find_element(By.CSS_SELECTOR, 'a > div.champions-info > strong')
        img = champ.find_element(By.CSS_SELECTOR, 'a > div.tooltip.css-1tdngz6 > div > div > img').get_attribute('src')

        if name.text.replace(' ', '') == '노라와유미':
            save_champion_img('노라', img)
            continue

        save_champion_img(name, img)

    driver.quit()
