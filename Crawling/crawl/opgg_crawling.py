from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

import time

# op.gg 크롤링
def opgg_crawling():
    url = 'https://op.gg/ko/tft/meta-trends/comps'
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
        meta_title.append(meta.find_element(By.CSS_SELECTOR, 'div.flex.items-center.gap-1.text-\[12px\].leading-\[16px\].text-gray-0.md\:w-full.md\:gap-\[8px\].md\:text-\[14px\].md\:leading-\[20px\] > strong').text)
        meta_champ.append([champ.get_attribute('alt') for champ in meta.find_elements(By.CSS_SELECTOR, 'div > div:nth-child(2) > div:nth-child(2) > div > div:nth-child(2) > div > img')])

        act = ActionChains(driver)
        act.move_to_element(meta.find_element(By.CSS_SELECTOR, 'div.flex.w-full.flex-row.items-center.justify-between.gap-2.md\:basis-\[400px\].md\:flex-col.md\:items-start.md\:px-0.md\:py-\[15px\].md\:pr-\[16px\] > button')).click().perform()
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    detail_meta = driver.find_elements(By.CSS_SELECTOR, 'div > div.flex.h-\[192px\].w-full.flex-col.items-center.justify-center.md\:mt-1.md\:h-auto.md\:justify-start')
    print('디테일', detail_meta)

    for detail in detail_meta:
        detail_champion = detail.find_elements(By.CSS_SELECTOR, 'div.\-mt-2.flex.gap-1.first\:mt-0.md\:gap-2.\[\&\:nth-child\(even\)\]\:ml-\[22px\].md\:\[\&\:nth-child\(even\)\]\:ml-10 > div')
        location = {}
        item = {}
        star = {}
        for index, champion in enumerate(detail_champion, 1):
            champ_location = champion.find_elements(By.CSS_SELECTOR, 'div > div > div > img')

            # 챔피언이 있으면 위치 추출
            if champ_location:
                name = champ_location[0].get_attribute('alt')
                location[name] = index

                # 아이템 추출
                item_data = champion.find_elements(By.CSS_SELECTOR, 'div.absolute.bottom-0.z-10.flex.w-full.items-center.justify-center.gap-px > div > div > img')

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

    # 최종 메타 데이터 구성
    for num in range(len(meta_title)):
        meta_data[meta_title[num]] = {
            '챔프': meta_champ[num],
            '별': meta_champ_star[num],
            '위치': meta_champ_location[num],
            '아이템': meta_champ_item[num]
        }
    
    return meta_data