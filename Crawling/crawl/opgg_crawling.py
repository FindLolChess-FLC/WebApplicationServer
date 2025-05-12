from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

import time

# op.gg 크롤링
def opgg_crawling():
    url = 'https://op.gg/ko/tft/meta-trends/comps'
    
    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    options.set_preference("general.useragent.override",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(1)
    
    language = driver.find_element(By.CSS_SELECTOR, 'div.DetectLocale-module_btn-wrapper__5auv9 > button:nth-child(1)')
    language_selector = driver.find_element(By.CSS_SELECTOR, 'button.DetectLocgiale-module_btn__kH7V7.DetectLocale-module_submit-btn__d4BJQ.Button-module_primary__C6Yja')

    act = ActionChains(driver)

    if language.text == '한국어':
        act.move_to_element(language_selector).click().perform()
        time.sleep(3)

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

        button = meta.find_element(By.CSS_SELECTOR, 'button.flex.h-full.w-full.flex-grow.items-end.justify-center.p-\[8px\].text-darkpurple-400.hover\:bg-darkpurple-800')
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(0.3)
        button.click()
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    detail_meta = driver.find_elements(By.CSS_SELECTOR, 'div.md\:mt-5.md\:flex.md\:h-\[284px\] > div')

    for detail in detail_meta:
        detail_champion = detail.find_elements(By.CSS_SELECTOR, 'div.\-mt-2.flex.gap-1.first\:mt-0.md\:gap-2.\[\&\:nth-child\(even\)\]\:ml-\[22px\].md\:\[\&\:nth-child\(even\)\]\:ml-10 > div')
        location = {}
        item = {}
        star = {}
        for index, champion in enumerate(detail_champion, 1):
            
            champ_location = champion.find_elements(By.CSS_SELECTOR, 'div.\[clip-path\:polygon\(0px_27\%\,_50\%_0px\,_100\%_27\%\,_100\%_73\%\,_50\%_100\%\,_0px_73\%\,_0px_27\%\)\] > div > img')

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