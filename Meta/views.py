from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion, Augmenter
from .serializer import ChampionSerializer, ItemSerializer, SynergySerializer, LolMetaSerializer, LolMetaChampionSerializer, AugmenterSerializer
from django.db.models import Q
import re


# 챔피언 조회
class ChampionSearch(APIView):
    def get(self, request):
        name = request.query_params.get('name')
        if name:
            champion_instance = Champion.objects.filter(name = name).first()
            
            if champion_instance:
                serializer = ChampionSerializer(champion_instance)       
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 챔피언이 없습니다'}, status=status.HTTP_404_NOT_FOUND)
                
        else:
            champions = Champion.objects.all().order_by('id') 
            serializer = ChampionSerializer(champions, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        

# 시너지 조회
class SynergySearch(APIView):
    def get(self, request):
        synergy = request.query_params.get('name')
        if synergy:
            synergy_instance = Synergy.objects.filter(name = synergy).first()

            if synergy_instance:
                serializer = SynergySerializer(synergy_instance)
                champion_data = [champ.name for champ in synergy_instance.champion_set.all()]
                data = {**serializer.data, 'champion': champion_data}

                return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 시너지가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            synergys = Synergy.objects.all().order_by('id')
            champion_instances =  [synergy_champ.champion_set.all() for synergy_champ in synergys]
            champion_data = [[champion.name for champion in champion_set] for champion_set in champion_instances]
            
            serializer = SynergySerializer(synergys, many=True)
            data = [{**synergy, 'champion': champion_data[index]} for index,synergy in enumerate(serializer.data)]
            return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)


# 아이템 조회
class ItemSearch(APIView):
    def get(self, request):
        item = request.query_params.get('name')
        if item:
            item_instance = Item.objects.filter(kor_name = item).first()

            if item_instance:
                serializer = ItemSerializer(item_instance)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 아이템이 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            items = Item.objects.all().order_by('id') 
            serializer = ItemSerializer(items, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        

# 메타 조회
class MetaSearch(APIView):
    def get(self, requeset):
        metas = LolMeta.objects.all().order_by('id')
        meta_champions = LolMetaChampion.objects.all()
        data = []

        for meta in metas:
            meta_data = {
                'meta': LolMetaSerializer(meta).data,
                'synergys': []
            }
            meta_synergy = {}

            for meta_champion in meta_champions:
                if meta.id == meta_champion.meta.id:
                    meta_data['champions'].append(LolMetaChampionSerializer(meta_champion).data)

                    synergys = meta_champion.champion.synergy.all()
                    items = meta_champion.item.all()

                    for synergy in synergys:
                        if synergy.name not in meta_synergy:
                            meta_synergy[synergy.name] = 0
                            meta_synergy[f'{synergy.name}의 효과'] = synergy.effect
                        meta_synergy[synergy.name] += 1

                    if len(items) > 0 :
                        for item in items:
                            if '상징' in item.kor_name :
                                synergy = ''.join(re.findall(r'[^ 상징]',item.kor_name))
                                meta_synergy[synergy] += 1

            meta_data['synergys'].append(meta_synergy)
            data.append(meta_data)

        return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
    
    def post(self, request):

        def find_db(data):
            # 첫 번째 키워드 검색
            first_keyword = data[0]
            results = LolMeta.objects.none()  # 초기화

            # 첫 번째 키워드에 따른 메타 정보 검색
            if Champion.objects.filter(name=first_keyword).exists():
                results = LolMeta.objects.filter(lolmetachampion__champion__name=first_keyword)
            if Augmenter.objects.filter(name=first_keyword).exists():
                results = LolMeta.objects.filter(augmenter__name=first_keyword)
            if Synergy.objects.filter(name=first_keyword).exists():
                results = LolMeta.objects.filter(lolmetachampion__champion__synergy__name=first_keyword)
            if LolMeta.objects.filter(title=first_keyword).exists():
                results = LolMeta.objects.filter(title=first_keyword)

            # 두 번째 및 세 번째 키워드 필터링
            for keyword in data[1:]:
                # 각 추가 키워드에 대해 결과 필터링
                results = results.filter(
                    Q(lolmetachampion__champion__name=keyword) |
                    Q(augmenter__name=keyword) |
                    Q(lolmetachampion__champion__synergy__name=keyword) |
                    Q(title=keyword)
                )

            return [lol_meta for lol_meta in results.distinct()] 

        search_data = list(map(lambda x:x.replace(' ',''), request.data['data'].split(',')))
        
        total_data = find_db(search_data)
            
        data = []

        for meta in total_data:
            meta_champion = LolMetaChampionSerializer(LolMetaChampion.objects.filter(meta__title=meta.title), many=True).data
            meta_data = {
                'meta': LolMetaSerializer(meta).data,
                'synergys': {},
            }
            for champion in meta_champion:
                champ_synergy = champion['champion']['synergy']

                for synergy in champ_synergy:
                    if synergy not in meta_data['synergys']:
                        meta_data['synergys'][synergy] = 0
                        meta_data['synergys'][f'{synergy}의 효과'] = Synergy.objects.get(name=synergy).effect
                    meta_data['synergys'][synergy] += 1

                if 'item' in champion:
                    champ_item = champion['item']

                    for item in champ_item:
                        if '상징' in item['kor_name'] :
                            synergy = ''.join(re.findall(r'[^ 상징]',item['kor_name']))
                            meta_data['synergys'][synergy] += 1

            data.append(meta_data)

        if data == []:
            return Response({'resultcode': 'FAIL', 'message': '잘못된 검색어 입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)


class AugmenterSearch(APIView):
    def get(self, request):
        augmenter_name = request.query_params.get('name')
        augmenter_tier = request.query_params.get('tier')

        if augmenter_tier:
            augmenter_instance = Augmenter.objects.filter(tier=augmenter_tier)
            if augmenter_instance:
                serializer = AugmenterSerializer(augmenter_instance, many=True)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 티어가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        if augmenter_name:
            augmenter_instance = Augmenter.objects.filter(name=augmenter_name).first()

            if augmenter_instance:
                serializer = AugmenterSerializer(augmenter_instance)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 증강체가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            augmenters = Augmenter.objects.all().order_by('tier') 
            serializer = AugmenterSerializer(augmenters, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        