from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

# op.gg 크롤링
def opgg_crawling():
    url = 'https://tft.op.gg/meta-trends/comps'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(1)
    
    # 메타 데이터 크롤링
    crawl_meta = driver.find_elements(By.CSS_SELECTOR, 'ul.flex.flex-col.gap-1 > li')
    meta_title = []
    meta_champ = []
    meta_champ_location = []
    meta_champ_item = []
    meta_champ_star = []
    meta_data = {} 

    # 챔프, 제목 정보 추출
    for meta in crawl_meta:
        driver.execute_script("arguments[0].scrollIntoView(true);", meta)
        meta_title.append(meta.find_element(By.CSS_SELECTOR, 'div > div > div:nth-child(3) > div.items-center > strong').text)
        meta_champ.append([champ.get_attribute('alt') for champ in meta.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(2) > div:nth-child(2) > div > div:nth-child(2) > div > img')])

        act = ActionChains(driver)
        act.move_to_element(meta.find_element(By.CSS_SELECTOR, 'div.flex.w-full.flex-row.items-center.justify-between.gap-2.md\:basis-\[400px\].md\:flex-col.md\:items-start.md\:px-0.md\:py-\[15px\].md\:pr-\[16px\] > button')).click().perform()
    
    detail_meta = driver.find_elements(By.CSS_SELECTOR, 'div.md\:mt-5.md\:flex.md\:h-\[284px\] > div')

    for detail in detail_meta:
        detail_champion = detail.find_elements(By.CSS_SELECTOR, 'div > div')
        location = {}
        item = {}
        star = {}
        for index, champion in enumerate(detail_champion, 1):
            
            champ_location = champion.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(2)')

            # 챔피언이 있으면 위치 추출
            if champ_location:
                name = champ_location[0].text
                location[name] = index

                # 아이템 추출
                item_data = champion.find_elements(By.CSS_SELECTOR, 'div > div.absolute > div > div > img')

                if item_data: 
                    detail_item = []

                    for champ_item in item_data:
                        detail_item.append(champ_item.get_attribute('alt'))
                    item[name] = detail_item

                # 별 추출
                champ_star = champion.find_elements(By.CSS_SELECTOR, 'div.absolute.-top-1.flex.w-full.items-center.justify-center > svg')
                
                if champ_star:
                    star[name] = len(champ_star)
                else:
                    star[name] = 2

        meta_champ_location.append(location)
        meta_champ_item.append(item)
        meta_champ_star.append(star)

    print(meta_champ_location)
    print(meta_champ_star)

    # 최종 메타 데이터 구성
    for num in range(len(meta_title)):
        meta_data[meta_title[num]] = {
            '챔프': meta_champ[num],
            '별': meta_champ_star[num],
            '위치': meta_champ_location[num],
            '아이템': meta_champ_item[num]
        }
    
    return meta_data