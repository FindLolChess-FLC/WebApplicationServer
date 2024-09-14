from django.urls import path
from .views import ChampionSearch

urlpatterns = [
    path('championsearch/', ChampionSearch.as_view()), # 챔피언 조회
]
