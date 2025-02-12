from .models import *
from django.db.models import Q

def is_integer(value):
    try:
        return isinstance(int(value), int)  
    except ValueError:
        return False

def find_db(data):
    if is_integer(data[0]):
        results = LolMeta.objects.filter(id=int(data[0]))
    else:
        # 첫 번째 키워드 검색
        first_keyword = data[0]
        cleand_keyword = data[0].replace(' ', '')
        results = LolMeta.objects.none()  # 초기화
        
        # 첫 번째 키워드에 따른 메타 정보 검색
        if Champion.objects.filter(Q(name=first_keyword) | Q(name=cleand_keyword)).exists():
            results = LolMeta.objects.filter(
                                            Q(lolmetachampion__champion__name=first_keyword) | 
                                            Q(lolmetachampion__champion__name=cleand_keyword))
        if Synergy.objects.filter(Q(name=first_keyword) | Q(name=cleand_keyword)).exists():
            results = LolMeta.objects.filter(
                                            Q(lolmetachampion__champion__synergy__name=first_keyword) |  
                                            Q(lolmetachampion__champion__synergy__name=cleand_keyword))
        if LolMeta.objects.filter(Q(title=first_keyword.strip()) | Q(title=cleand_keyword)).exists():
            results = LolMeta.objects.filter(
                                            Q(title=first_keyword.strip()) | 
                                            Q(title=cleand_keyword))

        # 두 번째 및 세 번째 키워드 필터링
        for keyword in data[1:]:
            # 각 추가 키워드에 대해 결과 필터링
            results = results.filter(
                Q(lolmetachampion__champion__name=keyword) | Q(lolmetachampion__champion__name=keyword.replace(' ', '')) |
                Q(lolmetachampion__champion__synergy__name=keyword) |  Q(lolmetachampion__champion__synergy__name=keyword.replace(' ', '')) |
                Q(title=keyword.strip()) | Q(title=keyword.replace(' ', ''))
            ).order_by('-like_count')

    return [lol_meta for lol_meta in results.distinct()] 