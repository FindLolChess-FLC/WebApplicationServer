from selenium import webdriver
from selenium.webdriver.common.by import By
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
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(30)
    
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

    # 각 링크에 대한 상세 정보 크롤링
    for link in meta_link:
        driver.get(link)
        driver.implicitly_wait(1)

        detail = driver.find_elements(By.CSS_SELECTOR, 'div.Board.css-y6vj5x.e1mgaavq0 > div')
        crawl_item_data = driver.find_elements(By.CLASS_NAME, 'css-13yc51h.erj04nc0' )
        detail_meta_champ = []
        detail_champ_star = {}
        detail_champ_item = {}
        item_translation = {}

        # 아이템 상세 정보 추출
        if crawl_item_data:
            for item in crawl_item_data:
                driver.execute_script("arguments[0].scrollIntoView(true);", item)
                item_img = item.find_element(By.CSS_SELECTOR, 'div.selectedItem > img').get_attribute('src')
                result_item = ''.join(re.findall(r'(?<=Item_)(.*?)(?=\.png)', item_img) or re.findall(r'items/([^/]+?)(?=_)', item_img))
                item_name = item.find_element(By.CSS_SELECTOR, 'div.selectedItem').text
                item_translation[result_item] = item_name

        for champ in detail:
            champ_text = champ.text.replace(' ', '')

            # 챔피언 이름이 공백이 아닌 경우에만 처리
            if champ_text:
                detail_meta_champ.append(champ_text)

                # 아이템 추출
                img_elements = champ.find_elements(By.TAG_NAME, 'img')
                if img_elements:  # img 태그가 있을 경우에만 처리
                    detail_champ_item[champ_text] = [
                        item_translation.get(
                            (re.findall(r'(?<=Item_)(.*?)(?=\.png)', i.get_attribute('src')) or 
                            re.findall(r'items/([^/]+?)(?=_)', i.get_attribute('src')) or 
                            [''])[0]
                        )
                        for i in img_elements
                    ]

                # 별 개수 추출
                star_elements = champ.find_elements(By.CSS_SELECTOR, 'div.css-11hlchy.e1k9xd3h2 > div')
                if star_elements:  # 별 관련 요소가 있을 경우에만 처리
                    detail_champ_star[champ_text] = sum(
                        len(star.find_elements(By.TAG_NAME, 'div')) for star in star_elements
                    )

        meta_champ.append(detail_meta_champ)

        # 챔프 위치 정보 추출
        meta_champ_location.append(
            {champ: index for index, champ in enumerate(detail_meta_champ, 1) if champ}
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

            champ_item = meta_data[data]['아이템'].get(champ_name, [])
            if len(champ_item) > 0 :
                for item in champ_item:
                    if Item.objects.filter(name=item).exists():
                        print(Item.objects.filter(name=item).first())
                        champion.item.add(Item.objects.filter(name=item).first())

        max_value = max(champ_star.values())
        max_keys = [key for key, value in champ_star.items() if value == max_value]

        meta.reroll_lv=reroll_lv(max(max_keys))
        meta.save()
