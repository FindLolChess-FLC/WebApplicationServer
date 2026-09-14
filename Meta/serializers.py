from rest_framework import serializers
from django.db.models import Prefetch
from .models import Champion, ChampionImg, Synergy, SynergyImg, Item, ItemImg, LolMeta, LolMetaChampion, Augmenter, AugmenterImg, MetaReaction, Comment


def meta_placements_queryset():
    """Load one meta's nested champion, trait, item, and image data in batches."""
    return (LolMetaChampion.objects
            .select_related('champion', 'champion__championimg')
            .prefetch_related(
                Prefetch('champion__synergy',
                         queryset=Synergy.objects.select_related('synergyimg')),
                Prefetch('item', queryset=Item.objects.select_related('itemimg')),
            )
            .order_by('champion__price'))


def meta_details_prefetch():
    return Prefetch('lolmetachampion_set', queryset=meta_placements_queryset())


# 챔피언 이미지
class ChampionImgSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ChampionImg
        fields = ['img_src'] 


# 챔피언
class ChampionSerializer(serializers.ModelSerializer):
    synergy = serializers.StringRelatedField(many=True) 
    img = ChampionImgSerializer(source='championimg', read_only=True)

    class Meta:
        model = Champion
        fields = ['name', 'price', 'synergy', 'img'] 

    # 응답 커스텀
    def to_representation(self, instance):
        # 시리얼라이즈된 데이터 가져오기
        representation = super().to_representation(instance)
        
        if not instance.synergy.exists():
            representation.pop('synergy')
        
        return representation


# 시너지 이미지
class SynergyImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = SynergyImg
        fields = ['img_src']


# 시너지
class SynergySerializer(serializers.ModelSerializer):
    img = SynergyImgSerializer(source='synergyimg', read_only=True)

    class Meta:
        model = Synergy
        fields = '__all__'


# 아이템 이미지
class ItemImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = ItemImg
        fields = ['img_src']


# 아이템
class ItemSerializer(serializers.ModelSerializer):
    img = ItemImgSerializer(source='itemimg', read_only=True)

    class Meta:
        model = Item
        fields = ['name','item1', 'item2', 'effect', 'img']


# 증강체 이미지
class AugmenterImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = AugmenterImg
        fields = ['img_src']


# 증강체
class AugmenterSerializer(serializers.ModelSerializer):
    img = ItemImgSerializer(source='augmenterimg', read_only=True)

    class Meta:
        model = Augmenter
        fields = ['name', 'effect', 'tier', 'img']


# 롤 메타 챔피언
class LolMetaChampionSerializer(serializers.ModelSerializer):
    champion = ChampionSerializer()
    item = ItemSerializer(many=True)
    
    class Meta:
        model = LolMetaChampion
        fields = ['champion', 'star', 'location', 'item']

    # 응답 커스텀
    def to_representation(self, instance):
        # 시리얼라이즈된 데이터 가져오기
        representation = super().to_representation(instance)
        
        if not instance.item.exists():
            representation.pop('item')
        
        return representation


# 롤 메타
class LolMetaSerializer(serializers.ModelSerializer):
    champions = serializers.SerializerMethodField()

    class Meta:
        model = LolMeta
        fields = ['id', 'title', 'like_count', 'dislike_count', 'reroll_lv', 'champions']

    def get_champions(self, instance):
        lol_meta_champions = getattr(instance, '_prefetched_objects_cache', {}).get(
            'lolmetachampion_set')
        if lol_meta_champions is None:
            lol_meta_champions = meta_placements_queryset().filter(meta=instance)
        return LolMetaChampionSerializer(lol_meta_champions, many=True).data

    # 응답 커스텀
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not representation['champions']:
            representation.pop('champions', None)

        return representation
    

# 반응
class ReactionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MetaReaction
        fields = ['lol_meta', 'is_like']


# 댓글
class CommentSerializer(serializers.ModelSerializer):
    lol_meta = serializers.SerializerMethodField()
    writer = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'lol_meta', 'writer', 'date', 'content']

    def get_lol_meta(self,obj):
        return obj.lol_meta.title
    
    def get_writer(self,obj):
        return obj.writer.nickname

    def get_content(self, obj):
        # Keep the source marker in storage so repeated crawls update the same
        # comment, but do not show the marker as part of the deck guidance.
        content = obj.content
        if obj.writer.is_superuser:
            for marker in ('[롤체지지 덱 설명]\n', '[OP.GG 덱 설명]\n',
                           '[tactics.tools 덱 팁]\n'):
                if content.startswith(marker):
                    return content[len(marker):]
        return content
