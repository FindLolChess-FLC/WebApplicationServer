from django.urls import path
from .views import SignInView, SignUpView, UpdateNicknameView

urlpatterns = [
    path('SignUp/', SignUpView.as_view()), # 회원가입
    path('SignIn/', SignInView.as_view()), # 로그인
    path('Update/', UpdateNicknameView.as_view()), # 유저 이메일, 닉네임 조회, 비밀번호 수정
]