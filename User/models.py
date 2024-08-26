from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        if not email:
            raise ValueError('올바른 이메일 형식이 아닙니다.')
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(
        email = email,
        is_staff = is_staff,
        is_superuser = is_superuser,
        is_active = True,
        date_joined = now,
        **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)
    

# 유저
class User(AbstractUser):
    username = None
    email = models.EmailField(max_length=255, unique=True)
    nickname = models.CharField(max_length=30, unique=True, null=False, blank=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']

    objects = UserManager()


# 토큰
class Token(models.Model):
    token = models.CharField(max_length=355)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.email}의 토큰'
        