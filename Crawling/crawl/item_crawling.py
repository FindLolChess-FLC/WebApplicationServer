from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import re
import itertools

from Meta.models import Item, ItemImg
from Crawling.utils import get_img_src
from Crawling.utils import item_translation

# 아이템 데이터 크롤링
def item_crawling():
    url = 'https://lolchess.gg/items/set14'
    driver = webdriver.Chrome()

    driver.get(url)
    driver.implicitly_wait(1)
    
    crawl_data = driver.find_elements(By.CSS_SELECTOR, 'td.name.css-17s55cr.efxas325')
    item_data = driver.find_elements(By.CSS_SELECTOR, 'td.name.css-17s55cr.efxas325 > div > div.relative.overflow-hidden')

    act = ActionChains(driver)

    img_data = get_img_src('아이템')

    for index, item in enumerate(item_data):
        act.move_to_element(item).perform()
        
        act_data = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'css-16emzv1.eosr60k1')))
        name_data = act_data.find_element(By.TAG_NAME,'strong').text
        effect_data = ''.join(list(itertools.chain([i.text for i in act_data.find_elements(By.TAG_NAME,'p')]))).replace('\n', ' ')
        detail_item_data = crawl_data[index].find_elements(By.CSS_SELECTOR, 'ul > li > div > div > img')
        
        if detail_item_data:
            detail_item = [''.join(re.findall(r"TFT_Item_([^\.]+)\.png", item.get_attribute('src'))) for item in detail_item_data]
            item1_data = item_translation(detail_item[0].lower())
            item2_data = item_translation(detail_item[1].lower())

            item_instance, created = Item.objects.get_or_create(name=name_data, item1=item1_data, item2=item2_data, effect=effect_data)
            ItemImg.objects.get_or_create(item=item_instance, img_src=img_data.get(item_instance.name.replace(' ', ''), 'empty'))
        else:
            item_instance, created = Item.objects.get_or_create(name = name_data, effect = effect_data)
            ItemImg.objects.get_or_create(item=item_instance, img_src=img_data.get(item_instance.name.replace(' ', ''), 'empty'))

    comb_url = 'https://lolchess.gg/items/set14/table'
    driver.get(comb_url)
    driver.implicitly_wait(10)

    comb_item_data = driver.find_elements(By.CSS_SELECTOR, ' tbody > tr:nth-child(1) > td ')
    comb_act = ActionChains(driver)

    for comb_item in comb_item_data[1:]:
        comb_act.move_to_element(comb_item).perform()
        act_data = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.css-16emzv1.eosr60k1')))

        kor_name = act_data.find_element(By.TAG_NAME, 'strong').text
        effect = act_data.find_element(By.TAG_NAME, 'p').text
        
        item_instance, created = Item.objects.get_or_create(name = kor_name, effect = effect)
        ItemImg.objects.get_or_create(item=item_instance, img_src=img_data.get(item_instance.name, 'empty'))
        
    driver.quit()
