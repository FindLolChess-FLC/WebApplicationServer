import cloudinary.api
from decouple import config
import unicodedata

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
def _champion_key(name):
    return ''.join(unicodedata.normalize('NFKC', name).split()).casefold()


def jacaard_similarity(data, data2):
    set_data = {_champion_key(name) for name in data}
    set_data2 = {_champion_key(name) for name in data2}
    union = set_data | set_data2
    return len(set_data & set_data2) / len(union) if union else 0.0


def similar_meta_champions(data, data2, prices, threshold=0.8):
    """Match roster variants while keeping high-cost carry replacements distinct."""
    left = {_champion_key(name) for name in data}
    right = {_champion_key(name) for name in data2}
    if not left or not right:
        return False
    if left == right:
        return True

    removed, added = left - right, right - left
    normalized_prices = {_champion_key(name): cost for name, cost in prices.items()}
    # A replacement of a 4+ cost unit usually changes the deck's main carry.
    if removed and added and any(normalized_prices.get(name, 3) >= 4
                                 for name in removed | added):
        return False

    if jacaard_similarity(left, right) >= threshold:
        return True
    # Plain Jaccard scores a one-unit swap in an eight-unit board as 7/9.
    # Treat one low-cost filler replacement as the same comp on 7+ unit boards.
    return (min(len(left), len(right)) >= 7
            and len(removed) == len(added) == 1
            and all(normalized_prices.get(name, 3) <= 2 for name in removed | added)
            and len(left & right) / min(len(left), len(right)) >= threshold)


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

def remove_duplicates_data(data1: dict, data2: dict, threshold=0.8, prices=None):
    """Preserve the first deck when its champion roster is equivalent.

    Inputs are not mutated. Each value must have a ``챔프`` list; callers may
    exclude summoned units before comparison.
    """
    if not 0 < threshold <= 1:
        raise ValueError('유사도 기준은 0보다 크고 1 이하여야 합니다.')
    merged = dict(data1)
    for key, value in data2.items():
        if key in merged:
            raise ValueError(f'중복 메타 덱 키: {key}')
        if any(similar_meta_champions(value['챔프'], old['챔프'], prices or {}, threshold)
               for old in merged.values()):
            continue
        merged[key] = value
    return merged
