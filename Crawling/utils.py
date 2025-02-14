import cloudinary.api
from decouple import config

# 데이터 리롤 레벨 찾기
def reroll_lv(level):
    if level == 1:
        return 5
    elif level == 2:
        return 6
    elif level == 3:
        return 7
    else:
        return 8
    
# 아이템 번역
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

# 자카드 유사도 
def jacaard_similarity(data, data2):
    set_data = set(data)
    set_data2 = set(data2)
    return float(len(set_data.intersection(set_data2)) / len(set_data.union(set_data2)))


# cloudnary 이미지 url 가져오기
def get_img_src(folder_name):
    cloudinary.config(
    cloud_name = config('CLOUDNARY_NAME'),
    api_key = config('CLOUDNARY_KEY'),
    api_secret = config('CLOUDNARY_SECRET'),
    
    )  
    response = cloudinary.api.resources(
        type="upload",  
        prefix=f'tft/{folder_name}', 
        max_results=400 
    )
    
    image_urls = {}
    for resource in response["resources"]:
        image_urls[resource['display_name']] = resource["secure_url"]

    return image_urls