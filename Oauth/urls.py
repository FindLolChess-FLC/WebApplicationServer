from django.urls import path
from .views import GoogleSigInView, GoogleSignInUrlView, KakaoSinginUrlView, KakaoSigninView, NaverSinginUrlView, NaverSigninView

urlpatterns = [
    path('google/login/', GoogleSignInUrlView.as_view()), # 구글 로그인 
    path('google/callback/', GoogleSigInView.as_view()), # 구글 로그인 완료 후 access token 발급
    path('kakao/login/', KakaoSinginUrlView.as_view()), # 카카오 로그인
    path('kakao/callback/', KakaoSigninView.as_view()), # 카카오 로그인 완료 후 access token 발급
    path('naver/login/', NaverSinginUrlView.as_view()), # 네이버 로그인
    path('naver/callback/', NaverSigninView.as_view()), # 네이버 로그인 완료 후 access token 발급
]