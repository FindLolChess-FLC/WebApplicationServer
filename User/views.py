from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.core.cache import cache
from .serializer import SignInSerializer, SignUpSerializer, UpdateNicknameSerializer, UpdatePasswordSerializer, DeleteIdSerializer
from .models import User
from .permission import IsAuthenticatedAndTokenVerified

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


