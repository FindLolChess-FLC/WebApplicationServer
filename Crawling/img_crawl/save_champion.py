from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
import os

def save_champion_img(name, img):
    save_directory = 'tft\챔피언'
    file_path = os.path.join(save_directory, f"{name.text.replace(' ', '')}.png")
    response = requests.get(img)
    with open(file_path, "wb") as file:
        file.write(response.content)

def save_champion():
    url = 'https://op.gg/ko/tft/meta-trends/champion'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)

    champ_data = driver.find_elements(By.CSS_SELECTOR,'tr.cursor-pointer > td:nth-child(2)')

    for champ in champ_data:
        name = champ.find_element(By.TAG_NAME, 'strong')
        img = champ.find_element(By.CSS_SELECTOR, 'div >div >div >div> img').get_attribute('src')

        save_champion_img(name, img)

    driver.quit()
