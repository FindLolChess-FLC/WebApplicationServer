from django.urls import path
from .views import ChampionSearch, SynergySearch, ItemSearch, MetaSearch, AugmenterSearch

urlpatterns = [
    path('championsearch/', ChampionSearch.as_view()), # 챔피언 조회
    path('synergysearch/', SynergySearch.as_view()), # 시너지 조회
    path('itemsearch/', ItemSearch.as_view()), # 아이템 조회
    path('metasearch/', MetaSearch.as_view()), # 메타 조회
    path('augmentersearch/', AugmenterSearch.as_view()), # 증강체 조회
]
