from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.core.mail import EmailMessage
from .serializer import SignInSerializer, SignUpSerializer, UpdateNicknameSerializer, UpdatePasswordSerializer, DeleteIdSerializer, EmailVerificationSerializer, FavoriteSerializer
from .models import User
from Meta.models import LolMeta
from .permission import IsAuthenticatedAndTokenVerified
import random
# Create your views here.

# 회원가입
class SignUpView(APIView):
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
    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = authenticate(email=request.data['email'], password=request.data['password'])

            if cache.get(user) == None:
                cache.set(user, {'access': data['access']})
                return Response({'resultcode': 'SUCCESS',
                                'access': data['access']}, status=status.HTTP_200_OK)
            
            return Response({'resultcode': 'FAIL', 'message': '이미 로그인된 유저입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'FAIL', 
                        'message': '로그인에 실패 했습니다.', 
                        'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# 닉네임 변경
class UpdateNicknameView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]
    def get(self, request):
        user = request.user
        serializer = UpdateNicknameSerializer(user)
        return Response({'resultcode': 'SUCCESS',
                        'email': user.email,
                        'nickname': serializer.data.get('nickname')}, status=status.HTTP_200_OK)
        
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
    def delete(self, request):
        try:
            cache.delete(request.user)
            return Response({'resultcode': 'SUCCESS', 'message': '로그아웃 성공'}, status=status.HTTP_200_OK)
        except:
            return Response({'resultcode': 'FAIL', 'message': '이미 로그아웃된 유저입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        

# 이메일 중복 체크
class EmailDuplicateView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response({'resultcode': 'FAIL', 'message': '중복된 이메일 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'SUCCESS', 'message': '사용 가능한 이메일 입니다.'}, status=status.HTTP_200_OK)
    

# 이메일 인증 코드
class EmailVerification(APIView):
    def get(self, request):
        to = request.query_params.get('email')
        if User.objects.filter(email=to).exists():
            return Response({'resultcode': 'FAIL', 'message': '중복된 이메일 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        subject = 'FLC-FindLolChess 인증 코드 입니다.'
        from_email = 'gns0314@naver.com'
        code = int(''.join(map(str,[random.randint(1, 9) for _ in range(4)])))
        message = f"""
                    <!DOCTYPE html>
                    <html lang="ko">
                    <head>
                        <meta charset="UTF-8">
                        <title>인증 코드</title>
                    </head>
                    <body>
                    <div style="background-color: #f0f0f0; padding: 5px;">
                        <div style="background-color: #ffffff;">
                            <h1>FLC-FindLolChess 인증 코드</h1>
                            <p>인증 코드는 <strong>{code}</strong>입니다.</p>
                            <p>이 코드를 입력하여 인증을 완료하세요.</p>
                        </div>
                    </div>
                    </body>
                    </html>
                    """
        email = EmailMessage(subject=subject, body=message, to=[to], from_email=from_email)
        email.content_subtype = 'html'  # 이메일 콘텐츠 타입을 HTML로 설정
        email.send()
        cache.set(to, code, timeout=180)

        return Response({'resultcode': 'SUCCESS', 'message': '인증코드가 발송 되었습니다.'}, status=status.HTTP_200_OK) 

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


# 닉네임 중복 체크
class NicknameDuplicateView(APIView):
    def post(self, request):
        nickname = request.data.get('nickname')
        if User.objects.filter(nickname=nickname).exists():
            return Response({'resultcode': 'FAIL', 'message': '중복된 닉네임 입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'resultcode': 'SUCCESS', 'message': '사용 가능한 닉네임 입니다.'}, status=status.HTTP_200_OK)
    

# 회원 탈퇴
class DeleteIdView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]
    def patch(self, request):
        user = request.user
        serializer = DeleteIdSerializer(user, data={'is_active':False})

        if serializer.is_valid():
            serializer.save()
            return Response({'resultcode': 'SUCCESS', 'message': '회원 탈퇴에 성공했습니다.'}, status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL',
                        'message': '회원 탈퇴에 실패 했습니다',
                        'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# 즐겨 찾기
class FavoriteView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    def get(self, request):
        user = request.user

        if user:
            serializer = FavoriteSerializer(user)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL',
                        'message': '올바르지 않은 유저입니다.',
                        'error': serializer.errors}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        user = request.user
        meta_id = request.data['id']
        
        if user:
            lol_meta = LolMeta.objects.get(id=meta_id)

            if lol_meta:
                user.favorite.add(lol_meta)
                return Response({'resultcode': 'SUCCESS', 'data': '즐겨찾기 성공'}, status=status.HTTP_200_OK)
            
            return Response({'resultcode': 'FAIL', 'message': '올바르지 않은 메타 아이디.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'resultcode': 'FAIL', 'message': '올바르지 않은 유저입니다.'}, status=status.HTTP_404_NOT_FOUND)