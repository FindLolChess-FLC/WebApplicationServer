from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
import itertools
from Meta.models import Item, ItemImg

# 조합 아이템 번역
def item_translation(data):
    if data == 'BFSword':
        return 'B.F.대검'
    elif data == 'RecurveBow':
        return '곡궁'
    elif data == 'ChainVest':
        return '쇠사슬 조끼'
    elif data == 'NegatronCloak':
        return '음전자 망토'
    elif data == 'NeedlesslyLargeRod':
        return '쓸데없이 큰 지팡이'
    elif data == 'Tearofthegoddess':
        return '여신의 눈물'
    elif data == 'GiantsBelt':
        return '거인의 허리띠'
    elif data == 'SparringGloves':
        return '연습용 장갑'
    elif data == 'Spatula':
        return '뒤집개'
    elif data == 'FryingPan':
        return '프라이팬'

# 아이템 데이터 크롤링
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
        item = list(itertools.chain(*[re.findall(r'(?<=Item_)(.*?)(?=\.png)', img.get_attribute('src')) for img in data]))
        all_item.append(item)

    act = ActionChains(driver)

    for act_num in range(len(effect_data)):
        act.move_to_element(effect_data[act_num]).perform()
        
        act_data = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CLASS_NAME, 'css-16emzv1.eosr60k1')))
        all_item[act_num].append(act_data.find_element(By.TAG_NAME,'strong').text)
        all_item[act_num].append(''.join(list(itertools.chain([i.text for i in act_data.find_elements(By.TAG_NAME,'p')]))).replace('\n', ' '))

    for detail_item in all_item:
        if len(detail_item) > 4:
            item_instance, created = Item.objects.get_or_create(name = detail_item[0], kor_name = detail_item[3], 
                                        kor_item1 = item_translation(detail_item[1]), item1 = detail_item[1],
                                        kor_item2 = item_translation(detail_item[2]), item2 = detail_item[2], 
                                        effect = detail_item[4])
            ItemImg.objects.get_or_create(item=item_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/아이템/{item_instance.kor_name.replace(' ','')}.png")
        else:
            item_instance, created = Item.objects.get_or_create(name = detail_item[0], kor_name = detail_item[1], effect = detail_item[2])
            ItemImg.objects.get_or_create(item=item_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/아이템/{item_instance.kor_name.replace(' ','')}.png")

    comb_url = 'https://lolchess.gg/items/set12'
    driver.get(comb_url)
    driver.implicitly_wait(10)

    comb_item_data = driver.find_elements(By.CSS_SELECTOR, '.css-uw2vh5.eqoykzw2 > button > div')
    comb_act = ActionChains(driver)

    for comb_item in comb_item_data:
        comb_act.move_to_element(comb_item).perform()
        act_data = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.css-16emzv1.eosr60k1')))

        name = ''.join(re.findall(r'(?:items|item)/([^/_.]+)', comb_item.find_element(By.TAG_NAME, 'img').get_attribute('src')))
        kor_name = act_data.find_element(By.TAG_NAME, 'strong').text
        effect = act_data.find_element(By.TAG_NAME, 'p').text
        
        item_instance, created = Item.objects.get_or_create(name = name, kor_name = kor_name, effect = effect)
        ItemImg.objects.get_or_create(item=item_instance, img_src=f"https://res.cloudinary.com/dcc862pgc/image/upload/f_auto,q_auto/v1/tft/아이템/{item_instance.kor_name.replace(' ','')}.png")
        
    driver.quit()
