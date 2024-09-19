from django.db import models
from User.models import User


class Synergy(models.Model):
    name = models.CharField(max_length=15)
    effect = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class SynergyImg(models.Model):
    synergy = models.OneToOneField(Synergy, on_delete=models.CASCADE)
    img_src = models.CharField(max_length=255)


class Item(models.Model):
    name = models.CharField(max_length=25)
    kor_name = models.CharField(max_length=25)
    effect = models.CharField(max_length=500)
    item1 = models.CharField(max_length=25)
    item2 = models.CharField(max_length=25)

    def __str__(self):
        return self.kor_name


class ItemImg(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    img_src = models.CharField(max_length=255)


class Champion(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField() 
    synergy = models.ManyToManyField(Synergy)

    def __str__(self):
        return self.name


class ChampionImg(models.Model):
    champion = models.OneToOneField(Champion, on_delete=models.CASCADE) 
    img_src = models.CharField(max_length=255)


class LolMeta(models.Model):
    title = models.CharField(max_length=50)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2)
    like_count = models.IntegerField(default=0) 
    dislike_count = models.IntegerField(default=0) 


class LolMetaChampion(models.Model):
    meta = models.ForeignKey(LolMeta, on_delete=models.CASCADE)
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE)
    star = models.IntegerField()  
    location = models.IntegerField() 
    item = models.ManyToManyField(Item)


class Comment(models.Model):
    lol_meta = models.ForeignKey(LolMeta, on_delete=models.CASCADE) 
    writer = models.ForeignKey(User, on_delete=models.CASCADE) 
    content = models.TextField()  
    created_at = models.DateTimeField(auto_now_add=True)
    