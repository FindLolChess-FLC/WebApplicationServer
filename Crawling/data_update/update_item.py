from Meta.models import ItemImg
from Crawling.utils import get_img_src

def update_item():
    item_data = ItemImg.objects.filter(img_src='empty')
    img_data = get_img_src('아이템')
    
    for item in item_data:
        item_name = item.item.name.replace(' ', '')
        item.img_src = img_data.get(item_name, '기본이미지경로')  

        item.save()