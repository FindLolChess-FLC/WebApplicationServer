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
    elif data == 'TearOfTheGoddess':
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

def remove_duplicates_data(data1:dict, data2:dict):
    data1_duplicate_keys = set()
    data2_duplicate_keys = set()
    non_duplicate_keys = []

    for d1_key, d1_value in data1.items():
        for d2_key, d2_value in data2.items():
            if jacaard_similarity(d1_value['챔프'], d2_value['챔프']) == 1:
                data1_duplicate_keys.add(d1_key)
                data2_duplicate_keys.add(d2_key)
                break 
            elif d1_key == d2_key:
                non_duplicate_keys.append(d2_key)

    for d1_key in data1_duplicate_keys:
        del data1[d1_key]

    for d2_key in data2_duplicate_keys:
        del data2[d2_key]
    
    for key in non_duplicate_keys:
        data2[f'{key}2'] = data2.pop(key)
    
    merge_meta_data = {**data1 , **data2}

    return merge_meta_data