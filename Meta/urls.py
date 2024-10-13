from django.urls import path
from .views import *

urlpatterns = [
    path('championsearch/', ChampionSearchView.as_view()), # 챔피언 조회
    path('synergysearch/', SynergySearchView.as_view()), # 시너지 조회
    path('itemsearch/', ItemSearchView.as_view()), # 아이템 조회
    path('metasearch/', MetaSearchView.as_view()), # 메타 조회
    path('augmentersearch/', AugmenterSearchView.as_view()), # 증강체 
    path('checkreaction/', CheckReactionView.as_view()), # 리액션 조회
    path('reaction/', ReactionView.as_view()), # 리액션 달기
    path('delreaction/', DeleteReactionView.as_view()), # 리액션 
    path('checkcomment/', CheckCommentView.as_view()), # 댓글 조회
    path('writecomment/', WriteCommentView.as_view()), # 댓글 작성
    path('updatecomment/', UpdateCommentView.as_view()), # 댓글 수정
    path('deletecomment/', DeleteCommentView.as_view()), # 댓글 삭제
]
