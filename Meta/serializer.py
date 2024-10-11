from rest_framework import serializers
from .models import Champion, ChampionImg, Synergy, SynergyImg, Item, ItemImg, LolMeta, LolMetaChampion, Augmenter, AugmenterImg

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
        fields = ['name', 'effect', 'img']


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
        fields = ['kor_name','kor_item1', 'kor_item2', 'effect', 'img']


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
    augmenter = AugmenterSerializer(many=True)
    lol_meta_champions = LolMetaChampionSerializer(source='lolmetachampion_set', many=True) 

    class Meta:
        model = LolMeta
        fields = ['id', 'title', 'augmenter', 'win_rate', 'like_count', 'dislike_count', 'lol_meta_champions'] 
    # 응답 커스텀
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        if not instance.augmenter.exists():
            representation.pop('augmenter')
        
        if not instance.lolmetachampion_set.exists(): 
            representation.pop('lol_meta_champions')
        
        return representation