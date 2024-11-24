from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.core.mail import EmailMessage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .serializers import SignInSerializer, SignUpSerializer, UpdateNicknameSerializer, UpdatePasswordSerializer, DeleteIdSerializer, EmailVerificationSerializer, FavoriteSerializer
from .models import User
from Meta.models import LolMeta
from .permission import IsAuthenticatedAndTokenVerified
from decouple import config
import random


# 회원가입
class SignUpView(APIView):
    @swagger_auto_schema(
    operation_description='회원 가입',
    operation_summary='회원 가입',
    operation_id='회원_가입',
    tags=['유저'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='이메일'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호'),
            'nickname': openapi.Schema(type=openapi.TYPE_STRING, description='닉네임'),
        },
        required=['email', 'password', 'nickname'],  
    ),
    responses={
        201: openapi.Response(
            description='성공적으로 회원가입을 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '회원가입에 성공했습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='회원가입에 실패했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '회원가입에 실패했습니다.'
                }
            }
        ),
    }
)
    
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'resultcode': 'SUCCESS',
                            'message': '회원가입에 성공했습니다.'}, status=status.HTTP_201_CREATED)
        
        return Response({'resultcode': 'FAIL',
                            'message': '회원가입에 실패했습니다.',
                            'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# 로그인
class SignInView(TokenObtainPairView):
    @swagger_auto_schema(
    operation_description='로그인',
    operation_summary='로그인',
    operation_id='회원_로그인',
    tags=['유저'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='이메일'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호'),
        },
        required=['email', 'password'],  
    ),
    responses={
        200: openapi.Response(
            description='성공적으로 로그인을 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'access': 'string'
                }
            }
        ),
        400: openapi.Response(
            description='로그인에 실패 했습니다.',
            examples={
                'application/json':{'resultcode': 'FAIL','message': '로그인에 실패 했습니다.', 'error': 'string'}
            }
        ),
    }
)
    
    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = authenticate(email=request.data['email'], password=request.data['password'])

            cache.set(user, {'access': data['access']})
            return Response({'resultcode': 'SUCCESS',
                            'access': data['access']}, status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL', 
                        'message': '로그인에 실패 했습니다.', 
                        'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# 닉네임 중복 체크
class NicknameDuplicateView(APIView):
    @swagger_auto_schema(
    operation_description='닉네임 중복 체크',
    operation_summary='닉네임 중복 체크',
    operation_id='닉네임_중복체크',
    tags=['닉네임'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'nickname': openapi.Schema(type=openapi.TYPE_STRING, description='닉네임'),
        },
        required=['nickname'],  
    ),
    responses={
        200: openapi.Response(
            description='사용 가능한 닉네임 입니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '사용 가능한 닉네임 입니다.'  
                }
            }
        ),
        400: openapi.Response(
            description='중복된 닉네임 입니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '중복된 닉네임 입니다.',
                }
            }
        ),
    }
)
    
    def post(self, request):
        nickname = request.data.get('nickname')
        if User.objects.filter(nickname=nickname).exists():
            return Response({'resultcode': 'FAIL', 'message': '중복된 닉네임 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'SUCCESS', 'message': '사용 가능한 닉네임 입니다.'}, status=status.HTTP_200_OK)
    


# 닉네임 변경
class UpdateNicknameView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]
    
    @swagger_auto_schema(
    operation_description='닉네임 조회',
    operation_summary='닉네임 조회',
    operation_id='닉네임_조회',
    tags=['닉네임'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    responses={
        200: openapi.Response(
            description='성공적으로 닉네임을 조회 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'email': 'string',
                    'nickname': 'string'
                }
            }
        ),
        404: openapi.Response(
            description='해당하는 유저가 없습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '해당하는 유저가 없습니다.'
                }
            }
        ),
    }
)
    
    def get(self, request):
        user = request.user
        if user:
            serializer = UpdateNicknameSerializer(user)
            return Response({'resultcode': 'SUCCESS',
                            'email': user.email,
                            'nickname': serializer.data.get('nickname')}, status=status.HTTP_200_OK)
    
        return Response({'resultcode': 'FAIL','message': '해당하는 유저가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
    @swagger_auto_schema(
    operation_description='닉네임 변경',
    operation_summary='닉네임 변경',
    operation_id='닉네임_변경',
    tags=['닉네임'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'nickname': openapi.Schema(type=openapi.TYPE_STRING, description='닉네임'),
        },
        required=['nickname'],  
    ),
    responses={
        200: openapi.Response(
            description='성공적으로 닉네임 변경을 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'email': 'string',
                    'nickname': 'string'
                }
            }
        ),
        400: openapi.Response(
            description='닉네임 변경에 실패했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '닉네임 변경에 실패했습니다.',
                    'error':'string'
                }
            }
        ),
    }
)
    
    def patch(self, request):
        user = request.user
        serializer = UpdateNicknameSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'resultcode': 'SUCCESS',
                            'message': '닉네임 변경에 성공했습니다.',
                            'email': user.email,
                            'nickname': serializer.data.get('nickname')}, status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL', 
                        'message': '닉네임 변경에 실패했습니다.',
                        'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# 비밀번호 변경
class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    @swagger_auto_schema(
    operation_description='비밀번호 변경',
    operation_summary='비밀번호 변경',
    operation_id='회원_비밀번호_변경',
    tags=['유저'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'current': openapi.Schema(type=openapi.TYPE_STRING, description='현재 비밀번호'),
            'new': openapi.Schema(type=openapi.TYPE_STRING, description='새로운 비밀번호'),
        },
        required=['current', 'new'],  
    ),
    responses={
        200: openapi.Response(
            description='성공적으로 비밀번호 변경을 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '비밀번호가 성공적으로 변경되었습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='현재 비밀번호가 일치하지 않습니다.',
            examples={
                'application/json': [
                {'resultcode': 'FAIL', 'message': '현재 비밀번호가 일치하지 않습니다.'},
                {'resultcode': 'FAIL', 'message': '비밀번호 변경에 실패했습니다.','error':'string'},
                ]
            }
        ),
    }
)
    
    def patch(self, request):
        user = request.user
        serializer = UpdatePasswordSerializer(data = request.data)

        if serializer.is_valid():
            current = serializer.data.get('current')
            new = serializer.data.get('new')
            if user.check_password(current):
                user.set_password(new)
                user.save()
                return Response({'resultcode': 'SUCCESS', 'message': '비밀번호가 성공적으로 변경되었습니다.'}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '현재 비밀번호가 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'resultcode': 'FAIL', 'message': '비밀번호 변경에 실패했습니다.', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# 로그아웃
class SignOutView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    @swagger_auto_schema(
    operation_description='로그아웃',
    operation_summary='로그아웃',
    operation_id='회원_로그아웃',
    tags=['유저'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    responses={
        200: openapi.Response(
            description='로그아웃에 성공 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '로그아웃에 성공 했습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='이미 로그아웃된 유저입니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '이미 로그아웃된 유저입니다.',
                }
            }
        ),
    }
)
    
    def delete(self, request):
        try:
            cache.delete(request.user)
            return Response({'resultcode': 'SUCCESS', 'message': '로그아웃에 성공 했습니다.'}, status=status.HTTP_200_OK)
        except:
            return Response({'resultcode': 'FAIL', 'message': '이미 로그아웃된 유저입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        

# 이메일 중복 체크
class EmailDuplicateView(APIView):
    @swagger_auto_schema(
    operation_description='이메일 중복 체크 ',
    operation_summary='이메일 중복 체크',
    operation_id='이메일_중복체크',
    tags=['이메일'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='이메일'),
        },
        required=['email'],  
    ),
    responses={
        200: openapi.Response(
            description='사용 가능한 이메일 입니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '사용 가능한 이메일 입니다.'
                }
            }
        ),
        400: openapi.Response(
            description='중복된 이메일 입니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '중복된 이메일 입니다.',
                }
            }
        ),
    }
)
    
    def post(self, request):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'resultcode': 'FAIL', 'message': '중복된 이메일 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'SUCCESS', 'message': '사용 가능한 이메일 입니다.'}, status=status.HTTP_200_OK)
    

# 이메일 인증 코드
class EmailVerification(APIView):
    @swagger_auto_schema(
    operation_description='이메일 인증 코드 발송',
    operation_summary='이메일 인증 코드 발송',
    operation_id='이메일_인증_발송',
    tags=['이메일'],
    manual_parameters=[
            openapi.Parameter(
                'email',
                openapi.IN_QUERY,
                description='인증할 이메일',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    responses={
        200: openapi.Response(
            description='인증코드가 발송 되었습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '인증코드가 발송 되었습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='중복된 이메일 입니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '중복된 이메일 입니다.',
                }
            }
        ),
    }
)
    
    def get(self, request):
        to = request.query_params.get('email')
        if User.objects.filter(email=to).exists():
            return Response({'resultcode': 'FAIL', 'message': '중복된 이메일 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        subject = 'FLC-FindLolChess 인증 코드 입니다.'
        from_email = config('EMAIL_HOST_USER')
        code = int(''.join(map(str,[random.randint(1, 9) for _ in range(4)])))
        message = f"""
                    <!DOCTYPE html>
                <html lang="ko">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>인증 코드</title>
                </head>
                <body style="margin: 0; padding: 0; background-color: #FFF; font-family: Pretendard;">
                    <table style="background-color: #FFF; width: 37.9375rem; height: 32.125rem; margin: auto;">
                        <tr>
                            <td align="center">
                                <table style="background: #FFF; width: 37.9375rem; height: 32.125rem; margin: auto; box-shadow: 0 0.25rem 0.375rem rgba(0, 0, 0, 0.1);">
                                    <tr>
                                        <td style="padding: 0;">
                                            <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700; color: #0D0D0D; margin: 1.8125rem 0 0 1.6875rem;border-bottom: 0.0625rem solid #0D0D0D; width: 34.625rem; padding-bottom: 0.75rem; font-style: normal; line-height: normal;">Find Lol Chess</h2>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="center">
                                            <h1 style="margin: 4.9375rem 0 2.6875rem 0; font-size: 1.625rem; font-style: normal; font-weight: 600; color: #0D0D0D; line-height: normal;">FLC 이메일 인증 안내</h1>
                                            <p style="margin: 0; font-size: 0.9375rem; font-size: 0.9375rem; font-style: normal; font-weight: 500; color: #0D0D0D; line-height: 135.196%">FLC_FindLolChess에서 이메일 주소 인증을 요청하셨습니다.</p>
                                            <p style="margin: 0 0 2.6875rem 0; font-size: 0.9375rem; font-style: normal; font-weight: 500; color: #0D0D0D; line-height: 135.196%">아래의 인증코드를 입력하여 인증을 완료해주세요.</p>
                                            <table style="background-color: #F7F7F7; text-align: center; margin: 0 auto 5.0625rem; width: 27.3125rem; height: 8.75rem;">
                                                <tr>
                                                    <td>
                                                        <p style="margin: 0 0 1.5rem 0; font-size: 0.9375rem; font-style: normal; font-weight: 600; color: #0D0D0D; line-height: normal;">로그인 승인 코드입니다.</p>
                                                        <strong style="font-size: 1.6875rem; font-style: normal; font-weight: 600; color: #5144ED; letter-spacing: 0.3125rem; line-height: normal;">{code}</strong>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr>
                                    <td align="center" style="padding: 20px; background-color: #FFF; font-size: 12px; color: #aaaaaa;">
                                        © 2024 Find Lol Chess. All rights reserved.
                                    </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                    """
        email = EmailMessage(subject=subject, body=message, to=[to], from_email=from_email)
        email.content_subtype = 'html'  # 이메일 콘텐츠 타입을 HTML로 설정
        email.send()
        cache.set(to, code, timeout=180)

        return Response({'resultcode': 'SUCCESS', 'message': '인증코드가 발송 되었습니다.'}, status=status.HTTP_200_OK) 

    @swagger_auto_schema(
    operation_description='이메일 인증 코드 확인',
    operation_summary='이메일 인증 코드 확인',
    operation_id='이메일_인증_확인',
    tags=['이메일'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='이메일'),
            'code': openapi.Schema(type=openapi.TYPE_STRING, description='인증번호'),
        },
        required=['email'],  
    ),
    responses={
        200: openapi.Response(
            description='인증에 성공 했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '인증에 성공 했습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='잘못된 요청입니다.',
            examples={
                'application/json': [
                    {'resultcode': 'FAIL', 'message': '인증시간이 만료되었습니다.'},
                    {'resultcode': 'FAIL', 'message': '잘못된 인증 코드 입니다.'},
                    {'resultcode': 'FAIL', 'message': '잘못된 정보 입니다.'},
                ]
            }
        ),
    }
)
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            if cache.get(serializer['email'].value) == None:
                return Response({'resultcode': 'FAIL', 'message': '인증시간이 만료되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if serializer['code'].value == cache.get(serializer['email'].value):
                cache.delete(serializer['email'].value)
                return Response({'resultcode': 'SUCCESS', 'message': '인증에 성공 했습니다.'}, status=status.HTTP_200_OK)
            
            return Response({'resultcode': 'FAIL', 'message': '잘못된 인증 코드 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'FAIL', 'message': '잘못된 정보 입니다.'}, status=status.HTTP_400_BAD_REQUEST)


# 회원 탈퇴
class DeleteIdView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    @swagger_auto_schema(
    operation_description='회원 탈퇴',
    operation_summary='회원 탈퇴',
    operation_id='회원_탈퇴',
    tags=['유저'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호'),
        },
        required=['password'],  
    ),
    responses={
        200: openapi.Response(
            description='회원 탈퇴에 성공했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '회원 탈퇴에 성공했습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='회원 탈퇴에 실패 했습니다',
            examples={
                'application/json': 
                    {'resultcode': 'FAIL', 
                    'message': '회원 탈퇴에 실패 했습니다'
                    },
                
            }
        ),
    }
)
    
    def patch(self, request):
        user = request.user
        current = request.data.get('password')

        if user.check_password(current):
            serializer = DeleteIdSerializer(user, data={'is_active':False})
            
            if serializer.is_valid():
                serializer.save()
                return Response({'resultcode': 'SUCCESS', 'message': '회원 탈퇴에 성공했습니다.'}, status=status.HTTP_200_OK)
        else:

            return Response({'resultcode': 'FAIL', 'message': '현재 비밀번호가 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'resultcode': 'FAIL',
                        'message': '회원 탈퇴에 실패 했습니다',
                        'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# 즐겨 찾기 조회
class CheckFavoriteView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    @swagger_auto_schema(
    operation_description='즐겨찾기 조회',
    operation_summary='즐겨찾기 조회',
    operation_id='즐겨찾기_조회',
    tags=['즐겨찾기'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    responses={
        200: openapi.Response(
            description='즐겨찾기 조회에 성공했습니다.',
            schema=FavoriteSerializer,
        ),
        404: openapi.Response(
            description='올바르지 않은 유저입니다.',
            examples={
                'application/json': 
                    {'resultcode': 'FAIL', 
                    'message': '올바르지 않은 유저입니다.',
                    'error': 'stirng'
                    },
                
            }
        ),
    }
)
    
    def get(self, request):
        user = request.user

        if user:
            serializer = FavoriteSerializer(user)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL',
                        'message': '올바르지 않은 유저입니다.',
                        'error': serializer.errors}, status=status.HTTP_404_NOT_FOUND)


# 즐겨 찾기 
class FavoriteView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    @swagger_auto_schema(
    operation_description='즐겨찾기 하기',
    operation_summary='즐겨찾기 하기',
    operation_id='즐겨찾기_하기',
    tags=['즐겨찾기'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_STRING, description='메타 아이디'),
        },
        required=['id'],  
    ),
    responses={
        200: openapi.Response(
            description='즐겨찾기에 성공했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '즐겨찾기에 성공했습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='이미 즐겨찾기 된 메타입니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '이미 즐겨찾기 된 메타입니다.'
                }
            }
        ),
        404: openapi.Response(
            description='잘못된 정보 입니다.',
            examples={
                'application/json': [
                    {'resultcode': 'FAIL', 'message': '올바르지 않은 유저입니다.'},
                    {'resultcode': 'FAIL', 'message': '올바르지 않은 메타아이디 입니다.'},
                    ]
                
            }
        ),
    }
)
    
    def post(self, request):
        user = request.user
        meta_id = request.data['id']
        
        if user:
            lol_meta = LolMeta.objects.get(id=meta_id)
            if not (user.favorite.filter(id=meta_id).exists()):

                if lol_meta:
                    user.favorite.add(lol_meta)
                    return Response({'resultcode': 'SUCCESS', 'data': '즐겨찾기에 성공했습니다.'}, status=status.HTTP_200_OK)
                
                return Response({'resultcode': 'FAIL', 'message': '올바르지 않은 메타 아이디입니다.'}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({'resultcode': 'FAIL', 'message': '이미 즐겨찾기 된 메타입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'FAIL', 'message': '올바르지 않은 유저입니다.'}, status=status.HTTP_404_NOT_FOUND)
    

# 즐겨 찾기 삭제
class DeleteFavoriteView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    @swagger_auto_schema(
    operation_description='즐겨찾기 삭제',
    operation_summary='즐겨찾기 삭제',
    operation_id='즐겨찾기_삭제',
    tags=['즐겨찾기'],
    manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="JWT 토큰이 필요합니다. 'Bearer <토큰>' 형식으로 입력하세요.",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_STRING, description='메타 아이디'),
        },
        required=['id'],  
    ),
    responses={
        200: openapi.Response(
            description='즐겨찾기 삭제에 성공했습니다.',
            examples={
                'application/json': {
                    'resultcode': 'SUCCESS',
                    'message': '즐겨찾기 삭제에 성공했습니다.'
                }
            }
        ),
        400: openapi.Response(
            description='이미 삭제된 메타입니다.',
            examples={
                'application/json': {
                    'resultcode': 'FAIL',
                    'message': '이미 삭제된 메타입니다.'
                }
            }
        ),
        404: openapi.Response(
            description='잘못된 정보 입니다.',
            examples={
                'application/json': [
                    {'resultcode': 'FAIL', 'message': '올바르지 않은 유저입니다.'},
                    {'resultcode': 'FAIL', 'message': '올바르지 않은 메타아이디 입니다.'},
                    ]
                
            }
        ),
    }
)
    
    def delete(self, request):
        user = request.user
        meta_id = request.data['id']
        meta = LolMeta.objects.filter(id=meta_id)

        if user:

            if user.favorite.filter(id=meta_id).exists():

                if meta.exists():
                    user.favorite.remove(meta[0])
                    return Response({'resultcode': 'SUCCESS', 'data': '즐겨찾기 삭제에 성공했습니다.'}, status=status.HTTP_200_OK)
                
                return Response({'resultcode': 'FAIL', 'message': '올바르지 않은 메타 아이디입니다.'}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({'resultcode': 'FAIL', 'message': '이미 삭제된 메타입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'resultcode': 'FAIL', 'message': '올바르지 않은 유저입니다.'}, status=status.HTTP_404_NOT_FOUND)
