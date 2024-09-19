from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import itertools
from Meta.models import Item

def item_crawling():
    url = 'https://lolchess.gg/meta/items?type=all'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(10)
    
    crawl_data = driver.find_elements(By.CLASS_NAME, 'css-1m59px.e1jv8n014')
    effect_data = driver.find_elements(By.CSS_SELECTOR, 'td.item > div > div.relative.overflow-hidden')

    item_data = [img.find_elements(By.TAG_NAME, 'img') for img in crawl_data]
    all_item = []
    
    for data in item_data:
        item = list(itertools.chain(*[re.findall(r'(?<=items/)[^_/]+', img.get_attribute('src')) for img in data]))
        all_item.append(item)

    act = ActionChains(driver)

    for act_num in range(len(effect_data)):
        act.move_to_element(effect_data[act_num]).perform()
        
        act_data = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'css-16emzv1.eosr60k1')))
        all_item[act_num].append(act_data.find_element(By.TAG_NAME,'strong').text)
        all_item[act_num].append(''.join(list(itertools.chain([i.text for i in act_data.find_elements(By.TAG_NAME,'p')]))).replace('\n', ' '))

    for detail_item in all_item:
        if len(detail_item) > 4:
            Item.objects.get_or_create(name = detail_item[0], item1 = detail_item[1], item2 = detail_item[2], kor_name = detail_item[3], effect = detail_item[4])
        else:
            Item.objects.get_or_create(name = detail_item[0], kor_name = detail_item[1], effect = detail_item[2])

