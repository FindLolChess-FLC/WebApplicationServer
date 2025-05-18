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
        first_keyword = data[0]
        cleaned_keyword = first_keyword.replace(' ', '')
        
        # 조건별 쿼리셋 생성
        champion_qs = LolMeta.objects.filter(
            Q(lolmetachampion__champion__name=first_keyword) |
            Q(lolmetachampion__champion__name=cleaned_keyword)
        )

        synergy_qs = LolMeta.objects.filter(
            Q(lolmetachampion__champion__synergy__name=first_keyword) |
            Q(lolmetachampion__champion__synergy__name=cleaned_keyword)
        )

        title_qs = LolMeta.objects.filter(
            Q(title__icontains=first_keyword.strip()) |
            Q(title__icontains=cleaned_keyword)
        )

        # 세 쿼리셋을 합쳐서 중복 제거
        combined_qs = LolMeta.objects.none()
        for qs in [champion_qs, synergy_qs, title_qs]:
            combined_qs = combined_qs | qs
        results = combined_qs.distinct()

        # 두 번째 및 세 번째 키워드로 추가 필터링
        for keyword in data[1:]:
            cleaned_kw = keyword.replace(' ', '')
            stripped_kw = keyword.strip()
            results = results.filter(
                Q(lolmetachampion__champion__name=keyword) |
                Q(lolmetachampion__champion__name=cleaned_kw) |
                Q(lolmetachampion__champion__synergy__name=keyword) |
                Q(lolmetachampion__champion__synergy__name=cleaned_kw) |
                Q(title=stripped_kw) |
                Q(title=cleaned_kw)
            )

        results = results.order_by('-like_count')

    return list(results.distinct())