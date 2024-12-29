from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
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
    
# op.gg 크롤링
def opgg_crawling():
    url = 'https://tft.op.gg/meta-trends/comps'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(30)
    
    # 메타 데이터 크롤링
    crawl_meta = driver.find_elements(By.CLASS_NAME, 'css-1ywivro')
    meta_title = []
    meta_champ = []
    meta_detail = []
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
            
            if len(champion.find_elements(By.CSS_SELECTOR, 'div')) > 2:
                name = champion.find_element(By.CLASS_NAME, 'css-1vg5gno').text
                location[name] = index

                # if champion.find_elements(By.CSS_SELECTOR, ' div.css-15npqbh > div > img'): 
                #     for champ_item in champion.find_elements(By.CSS_SELECTOR, ' div.css-15npqbh > div > img'):
                #         item[name] = champ_item.get_attribute('alt')

                if champion.find_elements(By.CSS_SELECTOR, '.hexagon-star > span'):
                    star[name] = len(champion.find_elements(By.CSS_SELECTOR, 'div.hexagon-star > span'))
                    print(len(champion.find_elements(By.CSS_SELECTOR, '.hexagon-star > span')))
                else:
                    star[name] = 2
                    print(2)

        meta_champ_location.append(location)
        meta_champ_item.append(item)
        meta_champ_star.append(star)

    print(meta_champ_star)
 