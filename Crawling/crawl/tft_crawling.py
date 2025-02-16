from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def tft_crawling():
    
    driver = webdriver.Chrome()
    url = 'https://www.metatft.com/comps'
    wait = WebDriverWait(driver, 10)
    driver.get(url)

    crawl_meta = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'CompRowWrapper')))
    detail_meta_link = []
    meta_title = []
    meta_champ = []
    meta_champ_location = []
    meta_champ_item = []
    meta_champ_star = []
    meta_data = {} 

    for meta in crawl_meta:
        driver.execute_script("arguments[0].scrollIntoView(true);", meta)
        meta_title.append(meta.find_element(By.CLASS_NAME, 'Comp_Title').text)

        # expand_button = meta.find_element(By.CLASS_NAME, 'ExpandImageContainer')
        # ActionChains(driver).move_to_element(expand_button).click().perform()
        
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'team-builder')))

    # print(meta_champ)
    # for detail in detail_meta:
    #     detail_champion = detail.find_elements(By.CSS_SELECTOR, 'svg > g')
    #     location = {}
    #     item = {}
    #     star = {}
