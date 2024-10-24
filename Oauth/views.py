from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.core.cache import cache
from decouple import config
import requests
import urllib.parse
from User.models import User
from User.serializer import SignInSerializer
import random

# 닉네임 중복시 뒤에 1~99999 랜덤 숫자 붙여주기
def generate_unique_nickname(nickname):
                while User.objects.filter(nickname=nickname).exists():
                    nickname = f'{nickname}{random.randint(1, 99999)}'
                return nickname
            

# 구글 로그인 url 발급
class GoogleSignInUrlView(APIView):
    def get(self, request):
        client_id = config('GOOGLE_KEY')
        redirect_uri = config('GOOGLE_REDIRECT_URI')
        scope = config('GOOGLE_SCOPE')
        response_type = config('GOOGLE_RESPONSE_TYPE')

        google_login_url = (
            f'https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_type={response_type}'
        )
        
        return redirect(google_login_url)


# 구글 로그인후 JWT 발급
class GoogleSigInView(APIView):
    def post(self, request):
        auth_code = urllib.parse.unquote(request.data.get('code'))
        data = {
            'code': auth_code,
            'client_id': config('GOOGLE_KEY'),
            'client_secret': config('GOOGLE_SECRET'),
            'redirect_uri': config('GOOGLE_REDIRECT_URI'),
            'grant_type': config('GOOGLE_GRANT_TYPE'),
        }

        access_response = requests.post('https://oauth2.googleapis.com/token', data=data)

        if access_response.status_code == 200:
            token_info = access_response.json()
            access_token = token_info.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers).json()
            email = user_response.get('email')
            nickname = user_response.get('name')

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                nickname = generate_unique_nickname(nickname)
                user = User.objects.create(email=email, nickname=nickname)
                user.set_unusable_password()
                user.save()

            token = SignInSerializer.get_token(user)
            access_token = str(token.access_token)

            if cache.get(user.email):
                return Response({'resultcode': 'FAIL','message': '이미 로그인 되어있습니다.'},status=status.HTTP_400_BAD_REQUEST)
            
            cache.set(user.email, {'access': access_token})
            data = {'email':email, 'nickname':nickname, 'access':access_token}
            return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
        else:
            return Response({'resultcode': 'FAIL',
                            'message': '올바르지 않은 인증 코드입니다.', 
                            'error': access_response.json()['error']}, status=access_response.status_code)


# 카카오 로그인 url 발급
class KakaoSinginUrlView(APIView):
    def get(self, request):
        client_id = config('KAKAO_KEY')
        redirect_uri = config('KAKAO_REDIRECT_URI')
        response_type = config('KAKAO_RESPONSE_TYPE')

        kakao_login_url = f'https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}'
        return redirect(kakao_login_url)
    

# 카카오 로그인 후 JWT 발급
class KakaoSigninView(APIView):
    def post(self, request):
        auth_code = urllib.parse.unquote(request.data.get('code'))
        data = {
            'code': auth_code,
            'client_id': config('KAKAO_KEY'),
            'client_secret': config('KAKAO_SECRET'),
            'redirect_uri': config('KAKAO_REDIRECT_URI'),
            'grant_type': config('KAKAO_GRANT_TYPE'),
        }

        access_response = requests.post('https://kauth.kakao.com/oauth/token', data=data)

        if access_response.status_code == 200:
            token_info = access_response.json()
            access_token = token_info.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get('https://kapi.kakao.com/v2/user/me', headers=headers).json()
            email = user_response['kakao_account'].get('email')
            nickname = user_response['kakao_account']['profile'].get('nickname')

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                nickname = generate_unique_nickname(nickname)
                user = User.objects.create(email=email, nickname=nickname)
                user.set_unusable_password()
                user.save()

            token = SignInSerializer.get_token(user)
            access_token = str(token.access_token)

            if cache.get(user.email):
                return Response({'resultcode': 'FAIL','message': '이미 로그인 되어있습니다.'},status=status.HTTP_400_BAD_REQUEST)
            
            cache.set(user.email, {'access': access_token})
            data = {'email':email, 'nickname':nickname, 'access':access_token}
            return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
        else:
            return Response({'resultcode': 'FAIL',
                            'message': '올바르지 않은 인증 코드입니다.', 
                            'error': access_response.json()['error']}, status=access_response.status_code)
