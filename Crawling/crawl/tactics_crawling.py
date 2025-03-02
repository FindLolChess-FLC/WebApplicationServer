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

    # 모든 데이터를 가져오기위해 스크롤을 더이상 데이터가 로딩안될때까지 내리기
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
        champ_item = {}
        champ_star = {}

        # 아이템 및 별 데이터 저장
        for champ in champ_data:
            name = champ.find_element(By.CSS_SELECTOR, 'img').get_attribute('alt').replace(' ','')
            item = champ.find_elements(By.CSS_SELECTOR, '.absolute.flex.justify-center.left-\\[-4px\\].css-nmhol0.flex > img')
            star = champ.find_elements(By.TAG_NAME, 'svg')

            if item:
                champ_item[name] = [item_name.get_attribute('alt').replace(' ','') for item_name in item]

            if star:
                champ_star[name] = 3
            else:
                champ_star[name] = 2

        meta_champ_item.append(champ_item)
        meta_champ_star.append(champ_star)
        detail_meta_link.append(meta.find_element(By.CSS_SELECTOR, 'div.flex.items-center.mt-\[-2px\] > div > a').get_attribute('href'))

    for sequence, detail_link in enumerate(detail_meta_link):
        driver.get(detail_link)

        location_data = driver.find_elements(By.CSS_SELECTOR, '#team-planner-svg > g > g')[::-1]
        champ_location = {}

        champ_name = []
        meta_champ_star_keys = list(meta_champ_star[sequence].keys())

        # flex챔피언과 디테일 챔피언이 다를 경우 디테일에 없는 flex 챔피언 제거
        for key in meta_champ_star_keys:
            if key not in champ_name:
                del meta_champ_star[sequence][key]

        # 위치 데이터 저장
        for index, location in enumerate(location_data,1):
            name = location.text.replace(' ', '')

            # 챔피언 이름 데이터 저장
            if name:
                champ_location[name] = index          
                champ_name.append(name)

                # 만약 별 데이터에 디테일 챔피언이 없는경우 추가
                if not meta_champ_star[sequence].get(name, None):
                    meta_champ_star[sequence][name] = 2

        meta_champ.append(champ_name)
        meta_champ_location.append(champ_location)
        
    for num in range(len(meta_title)):
        meta_data[meta_title[num]] = {
            '챔프': meta_champ[num],
            '별': meta_champ_star[num],
            '위치': meta_champ_location[num],
            '아이템': meta_champ_item[num]
        }
    
    return meta_data