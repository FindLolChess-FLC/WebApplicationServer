from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator


class Synergy(models.Model):
    name = models.CharField(max_length=15)
    effect = models.CharField(max_length=500)
    sequence = ArrayField(
        models.CharField(max_length=20), 
        blank=True,
        default=list
    )

    def __str__(self):
        return self.name


class SynergyImg(models.Model):
    synergy = models.OneToOneField(Synergy, on_delete=models.CASCADE)
    img_src = models.CharField(max_length=255)

    def __str__(self):
        return self.synergy.name


class Augmenter(models.Model):
    name = models.CharField(max_length=25)
    effect = models.CharField(max_length=500)
    tier = models.CharField(max_length=15)
    
    def __str__(self):
            return self.name


class AugmenterImg(models.Model):
    augmenter = models.OneToOneField(Augmenter, on_delete=models.CASCADE)
    img_src = models.CharField(max_length=255)

    def __str__(self):
        return self.augmenter.name


class Item(models.Model):
    name = models.CharField(max_length=50)
    effect = models.CharField(max_length=500)
    item1 = models.CharField(max_length=50, blank=True)
    item2 = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class ItemImg(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    img_src = models.CharField(max_length=255)

    def __str__(self):
        return self.item.name


class Champion(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)]) 
    synergy = models.ManyToManyField(Synergy, blank=True)

    def __str__(self):
        return self.name


class ChampionImg(models.Model):
    champion = models.OneToOneField(Champion, on_delete=models.CASCADE) 
    img_src = models.CharField(max_length=255)

    def __str__(self):
        return self.champion.name


class LolMeta(models.Model):
    title = models.CharField(max_length=50)
    like_count = models.IntegerField(default=0) 
    dislike_count = models.IntegerField(default=0) 
    reroll_lv = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class MetaReaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    lol_meta = models.ForeignKey(LolMeta, on_delete=models.CASCADE)
    is_like = models.BooleanField(default=False)  # True는 좋아요, False는 싫어요


class LolMetaChampion(models.Model):
    meta = models.ForeignKey(LolMeta, on_delete=models.CASCADE)
    champion = models.ForeignKey(Champion, on_delete=models.CASCADE)
    star = models.IntegerField()  
    location = models.IntegerField() 
    item = models.ManyToManyField(Item, blank=True)

    def __str__(self):
        return f'{self.meta.title} - {self.champion.name}'


class Comment(models.Model):
    writer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    lol_meta = models.ForeignKey(LolMeta, on_delete=models.CASCADE) 
    content = models.TextField(max_length=500)  
    date = models.DateTimeField(auto_now_add=True)