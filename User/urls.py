from django.contrib.auth import views as auth_views
from django.urls import path
from .views import SignInView, SignUpView, UpdateNicknameView, UpdatePasswordView, SignOutView, EmailDuplicateView, NicknameDuplicateView, DeleteIdView, EmailVerification, FavoriteView, CheckFavoriteView, DeleteFavoriteView

urlpatterns = [
    path('signup/', SignUpView.as_view()), # 회원가입
    path('signin/', SignInView.as_view()), # 로그인
    path('signout/', SignOutView.as_view()), # 로그아웃
    path('updateinfo/', UpdateNicknameView.as_view()), # 유저 이메일, 닉네임 조회, 변경
    path('updatepassword/', UpdatePasswordView.as_view()), # 비밀번호 변경
    path('emailduplicate/', EmailDuplicateView.as_view()), # 이메일 중복 체크
    path('nicknameduplicate/', NicknameDuplicateView.as_view()), # 닉네임 중복 체크
    path('deleteid/', DeleteIdView.as_view()), # 회원탈퇴
    path('verification/', EmailVerification.as_view()), # 인증 코드 발급 / 인증
    path('checkfavorite/', CheckFavoriteView.as_view()), # 즐겨찾기 조회
    path('favorite/', FavoriteView.as_view()), # 즐겨찾기 
    path('deletefavorite/', DeleteFavoriteView.as_view()), # 즐겨찾기 삭제
    # 비밀번호 초기화
    path(
        'passwordreset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
        ),
        name='password_reset'
    ),
    # 비밀번호 초기화 이메일 전송 후 확인
    path(
        'passwordreset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done'
    ),
    # 링크 클릭 후 새로운 비밀번호 입력
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
        ),
        name='password_reset_confirm'
    ),
    # 비밀번호 변경 완료
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete'
    ),
]