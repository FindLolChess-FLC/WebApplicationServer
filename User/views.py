from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .serializer import SignInSerializer, SignUpSerializer, UpdateNicknameSerializer
from .models import User, Token

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
            Token.objects.create(user=user, token=data['access'])
            return Response({'resultcode': 'SUCCESS',
                            'access': data['access']}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

# 닉네임 변경
class UpdateNicknameView(APIView):
    permission_classes = [IsAuthenticated]
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