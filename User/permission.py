from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache


class IsAuthenticatedAndTokenVerified(IsAuthenticated):
    def has_permission(self, request, view):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        token = auth_header.split(' ')[1]
        user = request.user
        if not super().has_permission(request, view):
            return False
        
        # 요청 유저에 해당하는 토큰이 있을경우 True 없으면 False
        if cache.get(user) != None:
            # 유저에 해당하는 토큰과 요청 토큰 비교 
            if token == cache.get(user)['access']:
                return True
            return False
        
        return False