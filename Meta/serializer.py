from rest_framework import serializers
from .models import Champion


class ChampionSerializer(serializers.ModelSerializer):
    synergy = serializers.StringRelatedField(many=True) 
    
    class Meta:
        model = Champion
        fields = ['id','name', 'price', 'synergy'] 
        