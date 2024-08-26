from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Token

# 회원가입
class SignUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'password', 'nickname']
        extra_kwargs = {
                'password': {'write_only': True} 
            }
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# 로그인시 jwt 토큰 발급
class SignInSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.email
        return token
    
    def validate(self, attrs):
        # 이메일로 사용자 찾기
        email = attrs.get('email')
        password = attrs.get('password')
        
        if (User.objects.filter(email=email).first()) is None:
            raise serializers.ValidationError({'resultcode': 'FAIL', 'message': '이메일이 틀렸습니다.'})

        # 이메일이 존재하는 경우, 비밀번호 확인
        if (authenticate(email=email, password=password)) is None:
            raise serializers.ValidationError({'resultcode': 'FAIL', 'message': '비밀번호가 틀렸습니다.'})

        # 이메일과 비밀번호가 모두 일치하는 경우
        data = super().validate(attrs)
        return data
    

# 닉네임 수정
class UpdateNicknameSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['nickname']

