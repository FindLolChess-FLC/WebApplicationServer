from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os

def save_synergy_img(name, img):
    save_directory = 'tft\시너지'
    file_path = os.path.join(save_directory, f"{name.replace(' ', '')}.svg")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_synergy():
    url = 'https://lolchess.gg/synergies/set14'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)
    synergy_data = driver.find_elements(By.CLASS_NAME, 'name.css-17s55cr.efxas325')
    duplicate_img = []
    
    for data in synergy_data:
        name = ''.join(data.find_element(By.CSS_SELECTOR, ' div > div.trait-stat > div').text.split(' ')[1:])
        img = data.find_element(By.CSS_SELECTOR, ' div > div.relative.css-e1nswt.e169ksf30 > img').get_attribute('src')
        
        if name not in duplicate_img:
            save_synergy_img(name, img)
            duplicate_img.append(name)
    
    driver.quit()