from django.urls import path
from .views import SignIn, SignUp

urlpatterns = [
    path('SignUp/', SignUp.as_view()), # 회원가입
    path('SignIn/', SignIn.as_view()) # 로그인
]