from django.urls import path
from .views import GoogleSigInView, GoogleSignInUrlView

urlpatterns = [
    path('api/auth/google/login/', GoogleSignInUrlView.as_view()), # 구글 로그인 url 발급
    path('api/auth/google/callback/', GoogleSigInView.as_view()), # access token 발급
]