from rest_framework import serializers
from .models import Champion, ChampionImg, Synergy, SynergyImg, Item, ItemImg, LolMeta, LolMetaChampion, Augmenter, AugmenterImg


class ChampionImgSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ChampionImg
        fields = ['img_src'] 


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


class SynergyImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = SynergyImg
        fields = ['img_src']


class SynergySerializer(serializers.ModelSerializer):
    img = SynergyImgSerializer(source='synergyimg', read_only=True)

    class Meta:
        model = Synergy
        fields = ['name', 'effect', 'img']


class ItemImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = ItemImg
        fields = ['img_src']


class ItemSerializer(serializers.ModelSerializer):
    img = ItemImgSerializer(source='itemimg', read_only=True)

    class Meta:
        model = Item
        fields = ['kor_name','kor_item1', 'kor_item2', 'effect', 'img']


class AugmenterImgSerializer(serializers.ModelSerializer):

    class Meta:
        model = AugmenterImg
        fields = ['img_src']



class AugmenterSerializer(serializers.ModelSerializer):
    img = ItemImgSerializer(source='augmenterimg', read_only=True)

    class Meta:
        model = Augmenter
        fields = ['name', 'effect', 'tier', 'img']


class LolMetaSerializer(serializers.ModelSerializer):
    augmenter = AugmenterSerializer(many=True)

    class Meta:
        model = LolMeta
        fields = ['title', 'augmenter','win_rate', 'like_count', 'dislike_count']

    # 응답 커스텀
    def to_representation(self, instance):
        # 시리얼라이즈된 데이터 가져오기
        representation = super().to_representation(instance)
        
        if not instance.augmenter.exists():
            representation.pop('augmenter')
        
        return representation


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