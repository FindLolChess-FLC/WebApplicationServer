from collections import defaultdict

from Meta.models import LolMetaChampion


def find_duplicate_lolmeta():
    meta_champion_map = defaultdict(list)

    # 전체 LolMetaChampion을 미리 조회
    all_meta_champs = LolMetaChampion.objects.select_related('champion', 'meta')

    # 메타별 챔피언 이름 모으기
    for m in all_meta_champs:
        meta_champion_map[m.meta_id].append(m.champion.name)

    # 챔피언 조합으로 그룹핑
    key_to_meta_ids = defaultdict(list)
    for meta_id, champ_names in meta_champion_map.items():
        key = tuple(sorted(champ_names))
        key_to_meta_ids[key].append(meta_id)

    # 중복 조합만 반환
    duplicates = {k: v for k, v in key_to_meta_ids.items() if len(v) > 1}
    return duplicates