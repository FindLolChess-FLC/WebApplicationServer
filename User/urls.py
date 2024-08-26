from django.urls import path
from .views import SignInView, SignUpView, UpdateNicknameView, UpdatePasswordView, SignOutView, EmailDuplicateView, NicknameDuplicateView, DeleteIdView

urlpatterns = [
    path('signup/', SignUpView.as_view()), # 회원가입
    path('signin/', SignInView.as_view()), # 로그인
    path('signout/', SignOutView.as_view()), # 로그아웃
    path('updateinfo/', UpdateNicknameView.as_view()), # 유저 이메일, 닉네임 조회, 비밀번호 수정
    path('updatepassword/', UpdatePasswordView.as_view()), # 비밀번호 변경
    path('emailduplicate/', EmailDuplicateView.as_view()), # 이메일 중복 체크
    path('nickduplicate/', NicknameDuplicateView.as_view()), # 닉네임 중복 체크
    path('deleteid/', DeleteIdView.as_view()), # 회원탈퇴
]