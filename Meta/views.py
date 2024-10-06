from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion, Augmenter
from .serializer import ChampionSerializer, ItemSerializer, SynergySerializer, LolMetaSerializer, LolMetaChampionSerializer
import re
import itertools

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
                'synergys': [],
                'champions': []
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
            search_data = []

            if Champion.objects.filter(name=data).exists():
                search_data.append([lol_meta.meta for lol_meta in LolMetaChampion.objects.filter(champion__name=data)])

            if Augmenter.objects.filter(name=data).exists():
                search_data.append([lol_meta.meta for lol_meta in LolMetaChampion.objects.filter(meta__augmenter__name=data)])

            if Synergy.objects.filter(name=data).exists():
                search_data.append([lol_meta.meta for lol_meta in LolMetaChampion.objects.filter(champion__synergy__name=data)])
                
            if LolMeta.objects.filter(title=data).exists():
                search_data.append([lol_meta.meta for lol_meta in LolMetaChampion.objects.filter(meta__title=data)])

            return list(set(itertools.chain.from_iterable(search_data)))

        total_data = find_db(request.data['data'])
        data = []

        for meta in total_data:
            meta_champion = LolMetaChampionSerializer(LolMetaChampion.objects.filter(meta__title=meta.title), many=True).data
            meta_data = {
                'meta': LolMetaSerializer(meta).data,
                'synergys': {},
                'champions': meta_champion
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

        