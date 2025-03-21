from django.contrib import admin
from .models import *


class LolMetaChampionInline(admin.TabularInline):
    model = LolMetaChampion
    extra = 0
    fields = ['champion', 'star', 'location', 'item']


class LolMetaAdmin(admin.ModelAdmin):
    inlines = [LolMetaChampionInline]  
    list_display = ('title', 'like_count', 'dislike_count')


admin.site.register(Synergy)
admin.site.register(SynergyImg)
admin.site.register(Champion)
admin.site.register(ChampionImg)
admin.site.register(Item)
admin.site.register(ItemImg)
admin.site.register(Augmenter)
admin.site.register(AugmenterImg)
admin.site.register(LolMeta, LolMetaAdmin)
admin.site.register(LolMetaChampion)
admin.site.register(Comment)
