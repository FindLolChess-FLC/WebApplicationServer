from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os

def save_synergy_img(name, img):
    save_directory = 'tft\시너지'
    file_path = os.path.join(save_directory, f"{name.text.replace(' ', '')}.svg")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_synergy():
    url = 'https://lolchess.gg/meta/traits?type=all'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)
    synergy_data = driver.find_elements(By.CLASS_NAME, 'css-spge78.e13mys794')
    duplicate_img = []
    
    for data in synergy_data:
        name = data.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(1)')
        img = data.find_element(By.CSS_SELECTOR, 'div.ChampionPortrait > div > img').get_attribute('src')
        
        if name not in duplicate_img:
            save_synergy_img(name, img)
            duplicate_img.append(name)
    
    driver.quit()