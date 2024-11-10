from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.core.cache import cache
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from decouple import config
from User.models import User
from User.serializers import SignInSerializer
import requests
import urllib.parse
import random
import uuid

# 닉네임 중복시 뒤에 1~99999 랜덤 숫자 붙여주기
def generate_unique_nickname(nickname):
    while User.objects.filter(nickname=nickname).exists():
        nickname = f'{nickname}{random.randint(1, 99999)}'
    return nickname


# 구글 로그인 url 발급
class GoogleSignInUrlView(APIView):
    @swagger_auto_schema(
        operation_description='구글 로그인',
        operation_summary='구글 로그인',
        operation_id='구글_로그인',
        tags=['소셜 로그인'],
        responses={
            200: openapi.Response(
                description='성공적으로 구글 로그인 URL을 조회했습니다.',
                examples={
                    'application/json': {
                        'resultcode': 'SUCCESS',
                        'login_url': 'string'
                    }
                },
            ),
        }
    )

    def get(self, request):
        client_id = config('GOOGLE_KEY')
        redirect_uri = config('GOOGLE_REDIRECT_URI')
        scope = config('GOOGLE_SCOPE')
        response_type = config('GOOGLE_RESPONSE_TYPE')

        google_login_url = (
            f'https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&scope={scope}'
        )
        
        return Response({'resultcode': 'SUCCESS', 'login_url': google_login_url}, status=status.HTTP_200_OK)


# 구글 로그인후 JWT 발급
class GoogleSigInView(APIView):
    @swagger_auto_schema(
        operation_description='구글 콜백',
        operation_summary='구글 콜백',
        operation_id='구글_콜백',
        tags=['소셜 로그인'],
        responses={
            200: openapi.Response(
            description='성공적으로 요청을 처리했습니다.'
            ),
            302: openapi.Response(
                description='구글 로그인 성공 또는 실패 시 리다이렉트됩니다.',
                examples={
                    'text/html': '리다이렉트 URL로 이동합니다.'
                },
            ),
        }
    )

    def get(self, request):
        auth_code = request.query_params.get('code')

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

            data = {'email': email, 'access': access_token}

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:

                if User.objects.filter(nickname=nickname).exists():
                    data['message'] = '닉네임이 중복되어 변경되었습니다.'
                    nickname = generate_unique_nickname(nickname)
                    data['nickname'] = nickname

                user = User.objects.create(email=email, nickname=nickname)
                data['nickname'] = nickname
                user.set_unusable_password()
                user.save()
                    
            token = SignInSerializer.get_token(user)
            access_token = str(token.access_token)

            uri = config('GOOGLE_REDIRECT_URI2')
            nickname = f"?nickname={data['nickname']}" if 'nickname' in data else ''
            message = f"&message={data['message']}" if 'message' in data else ''
            redirect_url = f'{uri}{nickname}{message}'
            
            cache.set(user.email, {'access': access_token})

            response = redirect(redirect_url)
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=False,
            )

            return response
        else:
            return redirect(f"{uri}?message=올바르지 않은 인증 코드입니다.&error={access_response.json()['error']}")


# 카카오 로그인 url 발급
class KakaoSinginUrlView(APIView):
    @swagger_auto_schema(
        operation_description='카카오 로그인',
        operation_summary='카카오 로그인',
        operation_id='카카오_로그인',
        tags=['소셜 로그인'],
        responses={
            200: openapi.Response(
                description='성공적으로 카카오 로그인 URL을 조회했습니다.',
                examples={
                    'application/json': {
                        'resultcode': 'SUCCESS',
                        'login_url': 'string'
                    }
                },
            ),
        }
    )

    def get(self, request):
        client_id = config('KAKAO_KEY')
        redirect_uri = config('KAKAO_REDIRECT_URI')
        response_type = config('KAKAO_RESPONSE_TYPE')

        kakao_login_url = f'https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}'
        return Response({'resultcode': 'SUCCESS', 'login_url': kakao_login_url}, status=status.HTTP_200_OK)
    

# 카카오 로그인 후 JWT 발급
class KakaoSigninView(APIView):
    @swagger_auto_schema(
        operation_description='카카오 콜백',
        operation_summary='카카오 콜백',
        operation_id='카카오_콜백',
        tags=['소셜 로그인'],
        responses={
            200: openapi.Response(
            description='성공적으로 요청을 처리했습니다.'
            ),
            302: openapi.Response(
                description='카카오 로그인 성공 또는 실패 시 리다이렉트됩니다.',
                examples={
                    'text/html': '리다이렉트 URL로 이동합니다.'
                },
            ),
        }
    )

    def get(self, request):
        auth_code = request.query_params.get('code')

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

            data = {'email':email, 'access':access_token}

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:

                if User.objects.filter(nickname=nickname).exists():
                    data['message'] = '닉네임이 중복되어 변경되었습니다.'
                    nickname = generate_unique_nickname(nickname)
                    data['nickname'] = nickname

                user = User.objects.create(email=email, nickname=nickname)
                data['nickname'] = nickname
                user.set_unusable_password()
                user.save()

                if user_response['kakao_account']['profile'].get('nickname') != user.nickname:
                    data['message'] = '닉네임이 중복되어 변경되었습니다.'
                

            token = SignInSerializer.get_token(user)
            access_token = str(token.access_token)

            uri = config('KAKAO_REDIRECT_URI2')
            nickname = f"?nickname={data['nickname']}" if 'nickname' in data else ''
            message = f"&message={data['message']}" if 'message' in data else ''
            redirect_url = f'{uri}{nickname}{message}'

            cache.set(user.email, {'access': access_token})

            response = redirect(redirect_url)
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=False,
            )

            return response
        else:
            return redirect(f"{uri}?message=올바르지 않은 인증 코드입니다.&error={access_response.json()['error']}")



# 네이버 로그인 url 발급
class NaverSinginUrlView(APIView):
    @swagger_auto_schema(
        operation_description='네이버 로그인',
        operation_summary='네이버 로그인',
        operation_id='네이버_로그인',
        tags=['소셜 로그인'],
        responses={
            200: openapi.Response(
                description='성공적으로 네이버 로그인 URL을 조회했습니다.',
                examples={
                    'application/json': {
                        'resultcode': 'SUCCESS',
                        'login_url': 'string'
                    }
                },
            ),
        }
    )

    def get(self, request):
        client_id = config('NAVER_KEY')
        redirect_uri = config('NAVER_REDIRECT_URI')
        response_type = config('NAVER_RESPONSE_TYPE')
        state = urllib.parse.quote(str(uuid.uuid4()))

        naver_login_url = f'https://nid.naver.com/oauth2.0/authorize?response_type={response_type}&client_id={client_id}&state={state}&redirect_uri={redirect_uri}'
        
        return Response({'resultcode': 'SUCCESS', 'login_url': naver_login_url}, status=status.HTTP_200_OK)
    

# 네이버 로그인 후 JWT 발급
class NaverSigninView(APIView):
    @swagger_auto_schema(
        operation_description='네이버 콜백',
        operation_summary='네이버 콜백',
        operation_id='네이버_콜백',
        tags=['소셜 로그인'],
        responses={
            200: openapi.Response(
            description='성공적으로 요청을 처리했습니다.'
            ),
            302: openapi.Response(
                description='네이버 로그인 성공 또는 실패 시 리다이렉트됩니다.',
                examples={
                    'text/html': '리다이렉트 URL로 이동합니다.'
                },
            ),
        }
    )

    def get(self, request):
        auth_code = urllib.parse.unquote(request.query_params.get('code'))
        state = urllib.parse.unquote(request.query_params.get('state'))

        data = {
            'code': auth_code,
            'client_id': config('NAVER_KEY'),
            'client_secret': config('NAVER_SECRET'),
            'redirect_uri': config('NAVER_REDIRECT_URI2'),
            'grant_type': config('NAVER_GRANT_TYPE'),
            'state': state
        }

        access_response = requests.post('https://nid.naver.com/oauth2.0/token', data=data)

        if 'access_token' in access_response.json():
            token_info = access_response.json()
            access_token = token_info.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get('https://openapi.naver.com/v1/nid/me', headers=headers).json()
            email = user_response['response'].get('email')
            nickname = user_response['response'].get('nickname')
            data = {'email':email, 'access':access_token}

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:

                if User.objects.filter(nickname=nickname).exists():
                    data['message'] = '닉네임이 중복되어 변경되었습니다.'
                    nickname = generate_unique_nickname(nickname)
                    data['nickname'] = nickname

                user = User.objects.create(email=email, nickname=nickname)
                data['nickname'] = nickname
                user.set_unusable_password()
                user.save()

            token = SignInSerializer.get_token(user)
            access_token = str(token.access_token)

            uri = config('KAKAO_REDIRECT_URI2')
            nickname = f"?nickname={data['nickname']}" if 'nickname' in data else ''
            message = f"&message={data['message']}" if 'message' in data else ''
            redirect_url = f'{uri}{nickname}{message}'
            
            cache.set(user.email, {'access': access_token})

            response = redirect(redirect_url)
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=False,
            )

            return response
        else:
            return redirect(f"{uri}?message=올바르지 않은 인증 코드입니다.&error={access_response.json()['error']}")
