from rest_framework import serializers
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion


class ChampionSerializer(serializers.ModelSerializer):
    synergy = serializers.StringRelatedField(many=True) 
    
    class Meta:
        model = Champion
        fields = ['name', 'price', 'synergy'] # 순서를 위해 all대신 원하는 순서로 설정


class SynergySerializer(serializers.ModelSerializer):

    class Meta:
        model = Synergy
        fields = ['name', 'effect']


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = ['kor_name','kor_item1', 'kor_item2', 'effect']


class LolMetaSerializer(serializers.ModelSerializer):

    class Meta:
        model = LolMeta
        fields = '__all__' 


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