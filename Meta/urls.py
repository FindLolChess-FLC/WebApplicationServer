from django.urls import path
from .views import ChampionSearch, SynergySearch, ItemSearch

urlpatterns = [
    path('championsearch/', ChampionSearch.as_view()), # 챔피언 조회
    path('synergysearch/', SynergySearch.as_view()), # 시너지 조회
    path('itemsearch/', ItemSearch.as_view()), # 아이템 조회
]
