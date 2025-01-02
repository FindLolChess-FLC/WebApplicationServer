from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains

# op.gg 크롤링
def opgg_crawling():
    url = 'https://tft.op.gg/meta-trends/comps'
    
    service = Service('/usr/local/bin/geckodriver')
    options = Options()
    options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
    options.add_argument("--headless")
    options.binary_location = '/usr/bin/firefox'
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(1)
    
    # 메타 데이터 크롤링
    crawl_meta = driver.find_elements(By.CLASS_NAME, 'css-1ywivro')
    meta_title = []
    meta_champ = []
    meta_champ_location = []
    meta_champ_item = []
    meta_champ_star = []
    meta_data = {} 

    # 챔프, 제목 정보 추출
    for meta in crawl_meta:
        driver.execute_script("arguments[0].scrollIntoView(true);", meta)
        meta_title.append(meta.find_element(By.CSS_SELECTOR, 'a > div.css-k267f7 > div.top-info > div.basic-info > div.title > strong').text)
        meta_champ.append([i.text for i in meta.find_elements(By.CSS_SELECTOR, 'a > div.css-1my6l2q > div.unit-list > div > div.square--size-semi-large.css-1be4v9m')])
        
        act = ActionChains(driver)
        act.move_to_element(meta.find_element(By.CLASS_NAME, 'btn-detail')).click().perform()
    
    detail_meta = driver.find_elements(By.CLASS_NAME, 'builder-container')

    for detail in detail_meta:
        detail_champion = detail.find_elements(By.CLASS_NAME, 'hexagon')
        location = {}
        item = {}
        star = {}

        for index, champion in enumerate(detail_champion, 1):
            
            # 챔피언이 있으면 위치 추출
            if len(champion.find_elements(By.CSS_SELECTOR, 'div')) > 2:
                name = champion.find_element(By.CLASS_NAME, 'css-1vg5gno').text
                location[name] = index

                # 아이템 추출
                if champion.find_elements(By.CSS_SELECTOR, ' div.css-15npqbh > div > img'): 
                    detail_item = []
                    for champ_item in champion.find_elements(By.CSS_SELECTOR, ' div.css-15npqbh > div > img'):
                        detail_item.append(champ_item.get_attribute('alt'))
                    item[name] = detail_item

                # 별 추출
                if champion.find_elements(By.CSS_SELECTOR, '.hexagon-star > span'):
                    star[name] = len(champion.find_elements(By.CSS_SELECTOR, 'div.hexagon-star > span'))
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