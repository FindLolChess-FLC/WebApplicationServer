from rest_framework import serializers
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion


class ChampionSerializer(serializers.ModelSerializer):
    synergy = serializers.StringRelatedField(many=True) 
    
    class Meta:
        model = Champion
        fields = ['id','name', 'price', 'synergy'] # 순서를 위해 all대신 원하는 순서로 설정


class SynergySerializer(serializers.ModelSerializer):

    class Meta:
        model = Synergy
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = Item
        fields = '__all__'


class LolMetaChampionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LolMetaChampion
        fields = '__all__'


class LolMetaSerializer(serializers.ModelSerializer):

    class Meta:
        model = LolMeta
        fields = '__all__' 