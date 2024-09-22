from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Champion, Synergy, Item
from .serializer import ChampionSerializer, ItemSerializer, SynergySerializer


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
            synergy_instance = Synergy.objects.filter(synergy = synergy).first()

            if serializer:
                serializer = SynergySerializer(synergy_instance)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 시너지가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            synergys = Synergy.objects.all().order_by('id') 
            serializer = SynergySerializer(synergys, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)


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
