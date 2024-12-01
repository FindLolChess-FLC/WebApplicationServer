from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import re
from Meta.models import * 

def reroll_lv(level):
    if level == 1:
        return 5
    elif level == 2:
        return 6
    elif level == 3:
        return 7
    else:
        return 8
    
# lolchess.gg 크롤링
def lolchess_crawling():
    url = 'https://lolchess.gg/meta'
    
    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(10)
    
    # 메타 데이터 크롤링
    crawl_meta = driver.find_elements(By.CSS_SELECTOR, 'div.css-s9pipd.e2kj5ne0 > div')
    crawl_meta_link = driver.find_elements(By.CSS_SELECTOR, 'div.css-cchicn.emls75t7 > div.link-wrapper > a')

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
            meta_champ.append([champ for champ in re.findall(r'\$\d+\s+(\S+)', ' '.join(re.split(r'\n', text.replace(' ', ''))))])

    # 각 링크에 대한 상세 정보 크롤링
    for link in meta_link:
        driver.get(link)
        driver.implicitly_wait(10)

        detail = driver.find_elements(By.CSS_SELECTOR, 'div.Board.css-lmthfr.e1mgaavq0 > div')
        detail_meta_champ = []
        detail_champ_star = {}
        detail_champ_item = {}

        for champ in detail:
            detail_meta_champ.append(champ.text.replace(' ', ''))

            if len(champ.text) > 0:
                # 이미지의 src에서 아이템 추출
                detail_champ_item[champ.text.replace(' ', '')] = [
                    re.findall(r'(?<=Item_)(.*?)(?=\.png)', i.get_attribute('src')) 
                    if len(re.findall(r'(?<=Item_)(.*?)(?=\.png)', i.get_attribute('src'))) > 0
                    else re.findall(r'items/([^/]+?)(?=_)', i.get_attribute('src')) 
                    for i in champ.find_elements(By.TAG_NAME, 'img') if i.get_attribute('src')
                ]
                detail_champ_star[champ.text.replace(' ', '')] = sum(len(star.find_elements(By.TAG_NAME, 'div')) for star in champ.find_elements(By.CSS_SELECTOR, 'div.css-11hlchy.e1k9xd3h2 > div'))

        # 챔프 위치 정보 추출
        meta_champ_location.append(
            {champ: index for index, champ in enumerate(detail_meta_champ[:-1], 1) if champ}
        )

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
    
    for data in meta_data:
        meta, craeted = LolMeta.objects.get_or_create(title = data)

        champ_star = {1:0, 2:0, 3:0, 4:0, 5:0} 
        for champ_name in meta_data[data]['챔프']:
            champion, created = LolMetaChampion.objects.get_or_create(meta = meta, 
                                                        champion = Champion.objects.get(name = champ_name),
                                                        star = meta_data[data]['별'][champ_name], 
                                                        location = meta_data[data]['위치'][champ_name])
            
            price = Champion.objects.get(name = champ_name).price

            champ_star[price] += meta_data[data]['별'][champ_name]

            champ_item = meta_data[data]['아이템'][champ_name]

            if len(champ_item) > 0 :
                if isinstance(item, list) and len(item) > 0:
                    for item in champ_item:
                        if Item.objects.filter(name=item[0]).exists():
                            champion.item.add(Item.objects.get(name=item[0]))

        max_value = max(champ_star.values())
        max_keys = [key for key, value in champ_star.items() if value == max_value]

        meta.reroll_lv=reroll_lv(max(max_keys))
        meta.save()
