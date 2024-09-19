from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Champion
from .serializer import ChampionSerializer

# 챔피언 조회
class ChampionSearch(APIView):
    def get(self, request):
        name = request.query_params.get('name')
        if name:
            serializer = ChampionSerializer(Champion.objects.get(name = request.query_params.get('name')))       
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            champions = Champion.objects.all()
            serializer = ChampionSerializer(champions, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        

