from django.contrib import admin
from django.utils.html import format_html, format_html_join
from .models import *


class LolMetaChampionInline(admin.TabularInline):
    model = LolMetaChampion
    extra = 0
    fields = ['champion', 'star', 'location', 'item']


class GuideBoardPreview:
    @admin.display(description='레벨별 배치')
    def board_preview(self, obj):
        if not obj.champions:
            return '본문 설명 (배치 없음)'
        rows = format_html_join('', '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>', (
            (slot.get('name', ''), slot.get('star', ''), slot.get('location', ''),
             ', '.join(slot.get('items', [])) or '없음')
            for slot in sorted(obj.champions, key=lambda slot: slot.get('location', 0))
        ))
        return format_html(
            '<table><thead><tr><th>챔피언</th><th>성급</th><th>위치 (1~28)</th>'
            '<th>아이템</th></tr></thead><tbody>{}</tbody></table>', rows)


class MetaGuideInline(GuideBoardPreview, admin.TabularInline):
    model = MetaGuide
    verbose_name = '덱 설명·레벨 배치'
    verbose_name_plural = '덱 설명·레벨 배치 (0레벨은 본문 설명)'
    extra = 0
    show_change_link = True
    can_delete = False
    fields = ('source', 'level', 'board_preview', 'content')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class LolMetaAdmin(admin.ModelAdmin):
    inlines = [LolMetaChampionInline, MetaGuideInline]
    list_display = ('id', 'title', 'default_level', 'like_count', 'dislike_count')
    search_fields = ('title',)
    list_filter = ('default_level',)


@admin.register(MetaGuide)
class MetaGuideAdmin(GuideBoardPreview, admin.ModelAdmin):
    list_display = ('meta', 'source', 'level', 'champion_count')
    list_filter = ('source', 'level')
    search_fields = ('meta__title', 'source_id', 'content')
    list_select_related = ('meta',)
    autocomplete_fields = ('meta',)
    readonly_fields = ('board_preview',)
    fields = ('meta', 'source', 'source_id', 'source_url', 'level',
              'content', 'board_preview', 'champions')

    @admin.display(description='챔피언 수')
    def champion_count(self, obj):
        return len(obj.champions)


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
