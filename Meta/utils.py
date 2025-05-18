from .models import *
from django.db.models import Q

def is_integer(value):
    try:
        return isinstance(int(value), int)  
    except ValueError:
        return False

def find_db(data):
    if is_integer(data[0]):
        return list(LolMeta.objects.filter(id=int(data[0])))

    first_keyword = data[0]
    cleaned_keyword = first_keyword.replace(' ', '')
    stripped_keyword = first_keyword.strip()

    # 첫 키워드 조건들을 하나의 Q로 묶음
    base_q = (
        Q(lolmetachampion__champion__name=first_keyword) |
        Q(lolmetachampion__champion__name=cleaned_keyword) |
        Q(lolmetachampion__champion__synergy__name=first_keyword) |
        Q(lolmetachampion__champion__synergy__name=cleaned_keyword) |
        Q(title__icontains=stripped_keyword) |
        Q(title__icontains=cleaned_keyword)
    )

    # 두 번째 이후 키워드는 Q 객체 리스트로 누적
    additional_qs = []
    for keyword in data[1:]:
        cleaned_kw = keyword.replace(' ', '')
        stripped_kw = keyword.strip()
        additional_qs.append(
            Q(lolmetachampion__champion__name=keyword) |
            Q(lolmetachampion__champion__name=cleaned_kw) |
            Q(lolmetachampion__champion__synergy__name=keyword) |
            Q(lolmetachampion__champion__synergy__name=cleaned_kw) |
            Q(title=stripped_kw) |
            Q(title=cleaned_kw)
        )

    # 최종 Q 병합
    final_q = base_q
    for q in additional_qs:
        final_q &= q  # AND 조건으로 누적

    results = LolMeta.objects.filter(final_q).order_by('-like_count').distinct()

    return list(results)
