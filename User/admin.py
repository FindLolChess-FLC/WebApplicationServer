from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    # Admin 목록 페이지에서 표시할 필드
    list_display = ('email', 'nickname', 'password', 'is_staff', 'is_superuser', 'is_active', 'date_joined')

    # 상세 페이지에서 표시할 필드 그룹화
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('nickname',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')}),
        ('Important dates', {'fields': ('date_joined',)}),
    )
    
    # 읽기 전용 필드 설정
    readonly_fields = ('date_joined',)

    # 사용자 추가 시 표시할 필드
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2'),
        }),
    )

    search_fields = ('email', 'nickname')
    ordering = ('email',)
    filter_horizontal = ()

# User 모델과 커스터마이즈된 UserAdmin 등록
admin.site.register(User, UserAdmin)