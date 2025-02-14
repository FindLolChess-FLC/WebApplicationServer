from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from Meta.models import Augmenter, AugmenterImg
from Crawling.utils import get_img_src

def augmenter_crawling():
    tier_data = ['silver', 'gold', 'prismatic']
    img_src = ['실버', '골드', '프리즘']

    for tier,src in zip(tier_data,img_src):
        url = f'https://lolchess.gg/augments/set13?type={tier}'
        img_data = get_img_src(f'증강/{src}')

        service = Service('/usr/local/bin/geckodriver')
        options = Options()
        options.set_preference("intl.accept_languages", "ko,ko-KR,ko-kr")
        options.add_argument("--headless")
        options.binary_location = '/usr/bin/firefox'
        driver = webdriver.Firefox(service=service, options=options)

        driver.get(url)
        driver.implicitly_wait(10)

        augment_names = driver.find_elements(By.CSS_SELECTOR, 'div.css-mbssy4.e110kr668 > div > span')
        augment_effects = driver.find_elements(By.CLASS_NAME, 'css-uh2eun.e110kr6612')
        
        for name, effect in zip(augment_names, augment_effects):
            if tier == 'silver' :
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text.replace('\n', ''), tier='Silver')
                if ':' in augment_instance.name:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=img_data[augment_instance.name.replace(':','')])
                else:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=img_data[augment_instance.name])

            elif tier == 'gold':
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='Gold')
                if ':' in augment_instance.name:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=img_data[augment_instance.name.replace(':','')])
                else:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=img_data[augment_instance.name])

            elif tier == 'prismatic':
                augment_instance, created = Augmenter.objects.get_or_create(name=name.text.replace(' ', ''), effect=effect.text, tier='prism')
                if ':' in augment_instance.name:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=img_data[augment_instance.name.replace(':','')])
                else:
                    AugmenterImg.objects.get_or_create(augmenter=augment_instance, img_src=img_data[augment_instance.name])

    driver.quit()