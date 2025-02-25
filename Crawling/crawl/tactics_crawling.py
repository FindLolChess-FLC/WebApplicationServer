from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def tactics_crawling():
    driver = webdriver.Chrome()
    url = 'https://tactics.tools/ko/team-compositions'
    driver.get(url)

    detail_meta_link = []
    meta_title = []
    meta_champ = []
    meta_champ_location = []
    meta_champ_item = []
    meta_champ_star = []
    meta_data = {} 

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break  

        last_height = new_height
        
    crawl_meta = driver.find_elements(By.CLASS_NAME, 'tc-summary-wrap')
    
    for meta in crawl_meta:
        meta_title.append(meta.find_element(By.CLASS_NAME, 'text-lg.pl-1.font-montserrat.font-semibold').text)
        champ_data = meta.find_elements(By.CSS_SELECTOR, '.flex > div.mx-\\[3px\\].sm\\:mx-\\[5px\\].flex-shrink-0.relative.flex.flex-col')
        champ_name = []
        champ_item = {}
        champ_star = {}

        for champ in champ_data:
            name = champ.find_element(By.CSS_SELECTOR, 'img').get_attribute('alt').replace(' ','')
            item = champ.find_elements(By.CSS_SELECTOR, '.absolute.flex.justify-center.left-\\[-4px\\].css-nmhol0.flex > img')
            star = champ.find_elements(By.TAG_NAME, 'svg')

            champ_name.append(name)

            if item:
                for item_name in item:
                    champ_item[name] = item_name.get_attribute('alt').replace(' ','')

            if star:
                champ_star[name] = 3
            else:
                champ_star[name] = 2

        meta_champ_item.append(champ_item)
        meta_champ.append(champ_name)
        meta_champ_star.append(champ_star)
        detail_meta_link.append(meta.find_element(By.CSS_SELECTOR, 'div.flex.items-center.mt-\[-2px\] > div > a').get_attribute('href'))

    for detail_link in detail_meta_link:
        driver.get(detail_link)

        location_data = driver.find_elements(By.CSS_SELECTOR, '#team-planner-svg > g > g')[::-1]

        champ_location = {}
        for index, location in enumerate(location_data,1):
            name = location.text.replace(' ', '')

            if name:
                champ_location[name] = index
    
        meta_champ_location.append(champ_location)

    for num in range(len(meta_title)):
        meta_data[meta_title[num]] = {
            '챔프': meta_champ[num],
            '별': meta_champ_star[num],
            '위치': meta_champ_location[num],
            '아이템': meta_champ_item[num]
        }
        
    return meta_data