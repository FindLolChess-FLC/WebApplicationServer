from rest_framework import serializers
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion, Augmenter


class ChampionSerializer(serializers.ModelSerializer):
    synergy = serializers.StringRelatedField(many=True) 
    
    class Meta:
        model = Champion
        fields = ['name', 'price', 'synergy'] 


class SynergySerializer(serializers.ModelSerializer):

    class Meta:
        model = Synergy
        fields = ['name', 'effect']


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ['kor_name','kor_item1', 'kor_item2', 'effect']


class AugmenterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Augmenter
        fields = ['name', 'effect', 'tier']


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