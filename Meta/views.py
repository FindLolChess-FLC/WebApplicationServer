from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion
from .serializer import ChampionSerializer, ItemSerializer, SynergySerializer, LolMetaSerializer, LolMetaChampionSerializer


# 챔피언 조회
class ChampionSearch(APIView):
    def get(self, request):
        name = request.query_params.get('name')
        if name:
            champion_instance = Champion.objects.filter(name = name).first()
            
            if serializer:
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
        synergy = request.query_params.get('synergy')
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
                "meta": LolMetaSerializer(meta).data,
                "synergys": [],
                "champions": []
            }
            meta_synergy = {}

            for meta_champion in meta_champions:
                if meta.id == meta_champion.meta.id:
                    meta_data['champions'].append(LolMetaChampionSerializer(meta_champion).data)

                    synergys = meta_champion.champion.synergy.all()
                    
                    for synergy in synergys:
                        if synergy.name not in meta_synergy:
                            meta_synergy[synergy.name] = 0
                            meta_synergy[f'{synergy.name}의 효과'] = synergy.effect
                        meta_synergy[synergy.name] += 1

            meta_data['synergys'].append(meta_synergy)
            data.append(meta_data)

        return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
    
    def post(self, request):
        pass

