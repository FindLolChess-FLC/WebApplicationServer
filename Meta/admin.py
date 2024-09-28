from django.contrib import admin
from .models import *


class LolMetaChampionInline(admin.TabularInline):
    model = LolMetaChampion
    extra = 0
    fields = ['champion', 'star', 'location', 'item']


class LolMetaAdmin(admin.ModelAdmin):
    inlines = [LolMetaChampionInline]  
    list_display = ('title', 'win_rate', 'like_count', 'dislike_count')


admin.site.register(Synergy)
admin.site.register(Champion)
admin.site.register(Item)
admin.site.register(LolMeta, LolMetaAdmin)
admin.site.register(LolMetaChampion)
