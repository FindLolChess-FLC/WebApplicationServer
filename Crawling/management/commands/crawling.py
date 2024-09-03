from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import re

# lolchess.gg 크롤링
def lolchess_crawling():
    url = 'https://lolchess.gg/meta'
    driver = webdriver.Chrome()

    driver.get(url)
    time.sleep(3)
    
    # 메타 데이터 크롤링
    crawl_meta = driver.find_elements(By.CSS_SELECTOR, 'div.css-s9pipd.e2kj5ne0 > div')
    crawl_meta_link = driver.find_elements(By.CSS_SELECTOR, 'div.css-1jardaz.emls75t6 > a')

    meta_link = [link.get_attribute('href') for link in crawl_meta_link]
    meta_title = []
    meta_champ = []
    meta_champ_location = []
    meta_champ_item = []
    meta_champ_star = []
    meta_data = {} 

    # 챔프, 제목 정보 추출
    for meta in crawl_meta:
        text = meta.text
        if '공략 더 보기' in text:
            meta_title.append(re.split(r'\n', text)[0])
            meta_champ.append(re.findall(r'\$\d+\s+(\S+)', ' '.join(re.split(r'\n', text))))

    # 각 링크에 대한 상세 정보 크롤링
    for link in meta_link:
        driver.get(link)
        detail = driver.find_elements(By.CSS_SELECTOR, 'div.Board.css-lmthfr.e1mgaavq0 > div')
        detail_meta_champ = []
        detail_champ_star = {}
        detail_champ_item = {}
        
        for champ in detail:
            detail_meta_champ.append(champ.text)

            if len(champ.text) > 0:
                # 이미지의 src에서 아이템 추출
                detail_champ_item[champ.text] = [
                    re.findall(r'(?<=items/)[^_/]+', i.get_attribute('src')) 
                    for i in champ.find_elements(By.TAG_NAME, 'img') if i.get_attribute('src')
                ]
                detail_champ_star[champ.text] = sum(len(i.find_elements(By.TAG_NAME, 'div')) for i in champ.find_elements(By.CSS_SELECTOR, 'div.css-11hlchy.e1k9xd3h2 > div'))

        # 챔프 위치 정보 추출
        meta_champ_location.append([
            i for i in enumerate(detail_meta_champ[:len(detail_meta_champ) - 1], 1) 
            if len(i[1]) > 0
        ])

        meta_champ_item.append(detail_champ_item)
        meta_champ_star.append(detail_champ_star)

    # 최종 메타 데이터 구성
    for num in range(len(meta_link)):
        meta_data[meta_title[num]] = {
            '챔프': meta_champ[num],
            '별': meta_champ_star[num],
            '위치': meta_champ_location[num],
            '아이템': meta_champ_item[num]
        }
