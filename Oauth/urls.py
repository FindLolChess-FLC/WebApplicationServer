from django.urls import path
from .views import GoogleSigInView, GoogleSignInUrlView, KakaoSinginUrlView, KakaoSigninView

urlpatterns = [
    path('google/login/', GoogleSignInUrlView.as_view()), # 구글 로그인 
    path('google/callback/', GoogleSigInView.as_view()), # 구글 로그인 완료 후 access token 발급
    path('kakao/login/', KakaoSinginUrlView.as_view()), # 카카오 로그인
    path('kakao/callback/', KakaoSigninView.as_view()), # 카카오 로그인 완료 후 access token 발급
]