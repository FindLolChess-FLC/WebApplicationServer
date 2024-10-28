from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Champion, Synergy, Item, LolMeta, LolMetaChampion, Augmenter, MetaReaction, Comment
from .serializer import ChampionSerializer, ItemSerializer, SynergySerializer, LolMetaSerializer, LolMetaChampionSerializer, AugmenterSerializer, ReactionSerializer, CommentSerializer
from django.db.models import Q
from django.utils import timezone
from User.permission import IsAuthenticatedAndTokenVerified
import re

# 챔피언 조회
class ChampionSearchView(APIView):
    def get(self, request):
        name = request.query_params.get('name')
        if name:
            champion_instance = Champion.objects.filter(name = name).first()
            
            if champion_instance:
                serializer = ChampionSerializer(champion_instance)       
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 챔피언이 없습니다'}, status=status.HTTP_404_NOT_FOUND)
                
        else:
            champions = Champion.objects.all().order_by('id') 
            serializer = ChampionSerializer(champions, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        

# 시너지 조회
class SynergySearchView(APIView):
    def get(self, request):
        synergy = request.query_params.get('name')
        if synergy:
            synergy_instance = Synergy.objects.filter(name = synergy).first()

            if synergy_instance:
                serializer = SynergySerializer(synergy_instance)
                champion_data = [champ.name for champ in synergy_instance.champion_set.all()]
                data = {**serializer.data, 'champion': champion_data}

                return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 시너지가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            synergys = Synergy.objects.all().order_by('id')
            champion_instances =  [synergy_champ.champion_set.all() for synergy_champ in synergys]
            champion_data = [[champion.name for champion in champion_set] for champion_set in champion_instances]
            
            serializer = SynergySerializer(synergys, many=True)
            data = [{**synergy, 'champion': champion_data[index]} for index,synergy in enumerate(serializer.data)]
            return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)


# 아이템 조회
class ItemSearchView(APIView):
    def get(self, request):
        item = request.query_params.get('name')
        if item:
            item_instance = Item.objects.filter(kor_name = item).first()

            if item_instance:
                serializer = ItemSerializer(item_instance)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 아이템이 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            items = Item.objects.all().order_by('id') 
            serializer = ItemSerializer(items, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        

# 메타 조회
class MetaSearchView(APIView):
    def get(self, requeset):
        metas = LolMeta.objects.all().order_by('id')
        meta_champions = LolMetaChampion.objects.all()
        data = []

        for meta in metas:
            meta_data = {
                'meta': LolMetaSerializer(meta).data,
                'synergys': []
            }
            meta_synergy = {}

            for meta_champion in meta_champions:
                
                if meta.id == meta_champion.meta.id:
                    synergys = meta_champion.champion.synergy.all()
                    items = meta_champion.item.all()

                    for synergy in synergys:
                        if synergy.name not in meta_synergy:
                            meta_synergy[synergy.name] = 0
                            meta_synergy[f'{synergy.name}의 효과'] = synergy.effect
                        meta_synergy[synergy.name] += 1

                    if len(items) > 0 :
                        for item in items:
                            if '상징' in item.kor_name :
                                synergy = ''.join(re.findall(r'[^ 상징]',item.kor_name))
                                meta_synergy[synergy] += 1

            meta_data['synergys'].append(meta_synergy)
            data.append(meta_data)

        return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)
    
    def post(self, request):

        def find_db(data):
            # 첫 번째 키워드 검색
            first_keyword = data[0]
            cleand_keyword = data[0].replace(' ', '')
            results = LolMeta.objects.none()  # 초기화
            
            # 첫 번째 키워드에 따른 메타 정보 검색
            if Champion.objects.filter(Q(name=first_keyword) | Q(name=cleand_keyword)).exists():
                results = LolMeta.objects.filter(
                                                Q(lolmetachampion__champion__name=first_keyword) | 
                                                Q(lolmetachampion__champion__name=cleand_keyword))
            if Augmenter.objects.filter(Q(name=first_keyword) | Q(name=cleand_keyword)).exists():
                results = LolMeta.objects.filter(
                                                Q(augmenter__name=first_keyword) | 
                                                Q(augmenter__name=cleand_keyword))
            if Synergy.objects.filter(Q(name=first_keyword) | Q(name=cleand_keyword)).exists():
                results = LolMeta.objects.filter(
                                                Q(lolmetachampion__champion__synergy__name=first_keyword) |  
                                                Q(lolmetachampion__champion__synergy__name=cleand_keyword))
            if LolMeta.objects.filter(Q(title=first_keyword.strip()) | Q(title=cleand_keyword)).exists():
                results = LolMeta.objects.filter(
                                                Q(title=first_keyword.strip()) | 
                                                Q(title=cleand_keyword))

            # 두 번째 및 세 번째 키워드 필터링
            for keyword in data[1:]:
                # 각 추가 키워드에 대해 결과 필터링
                results = results.filter(
                    Q(lolmetachampion__champion__name=keyword) | Q(lolmetachampion__champion__name=keyword.replace(' ', '')) |
                    Q(augmenter__name=keyword) | Q(augmenter__name=keyword.replace(' ', '')) |
                    Q(lolmetachampion__champion__synergy__name=keyword) |  Q(lolmetachampion__champion__synergy__name=keyword.replace(' ', '')) |
                    Q(title=keyword.strip()) | Q(title=keyword.replace(' ', ''))
                )

            return [lol_meta for lol_meta in results.distinct()] 

        search_data = request.data['data'].split(',')
        
        total_data = find_db(search_data)
            
        data = []

        for meta in total_data:
            meta_champion = LolMetaChampionSerializer(LolMetaChampion.objects.filter(meta__title=meta.title), many=True).data
            meta_data = {
                'meta': LolMetaSerializer(meta).data,
                'synergys': {},
            }
            for champion in meta_champion:
                champ_synergy = champion['champion']['synergy']

                for synergy in champ_synergy:
                    if synergy not in meta_data['synergys']:
                        meta_data['synergys'][synergy] = 0
                        meta_data['synergys'][f'{synergy}의 효과'] = Synergy.objects.get(name=synergy).effect
                    meta_data['synergys'][synergy] += 1

                if 'item' in champion:
                    champ_item = champion['item']

                    for item in champ_item:
                        if '상징' in item['kor_name'] :
                            synergy = ''.join(re.findall(r'[^ 상징]',item['kor_name']))
                            meta_data['synergys'][synergy] += 1

            data.append(meta_data)

        if data == []:
            return Response({'resultcode': 'FAIL', 'message': '잘못된 검색어 입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'resultcode': 'SUCCESS', 'data': data}, status=status.HTTP_200_OK)

# 증강체 조회
class AugmenterSearchView(APIView):
    def get(self, request):
        augmenter_name = request.query_params.get('name')
        augmenter_tier = request.query_params.get('tier')

        if augmenter_tier:
            augmenter_instance = Augmenter.objects.filter(tier=augmenter_tier)
            if augmenter_instance:
                serializer = AugmenterSerializer(augmenter_instance, many=True)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 티어가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        if augmenter_name:
            augmenter_instance = Augmenter.objects.filter(name=augmenter_name).first()

            if augmenter_instance:
                serializer = AugmenterSerializer(augmenter_instance)
                return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({'resultcode': 'FAIL', 'message': '해당하는 증강체가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            augmenters = Augmenter.objects.all().order_by('tier') 
            serializer = AugmenterSerializer(augmenters, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)

# 리액션 조회
class CheckReactionView(APIView):
    def get(self, request):
        user = request.user
        data = MetaReaction.objects.filter(user=user)
        if user:
            serializer = ReactionSerializer(data, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)


# 리액션 하기
class ReactionView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    def post(self, request):
        meta_id = request.data['id']
        if request.data['action'] == 'like':
            action = True
        elif request.data['action'] == 'dislike':
            action = False

        user = request.user

        if meta_id:
            meta_instance = LolMeta.objects.get(id=meta_id)

            if meta_instance:
                meta_reaction = MetaReaction.objects.filter(user=user, lol_meta=meta_instance)

                if meta_reaction:
                    if meta_reaction[0].is_like != action:
                        
                        if action == True:
                            meta_reaction.update(is_like = True)
                            meta_instance.like_count += 1
                            meta_instance.dislike_count -= 1

                        elif action == False:
                            meta_reaction.update(is_like = False)
                            meta_instance.dislike_count += 1
                            meta_instance.like_count -= 1

                        meta_instance.save()
                        return Response({'resultcode': 'SUCCESS', 'data': {'likes': meta_instance.like_count, 'dislikes': meta_instance.dislike_count}}, status=status.HTTP_200_OK)
                    
                    return Response({'resultcode': 'FAIL', 'message': '이미 리액션을 눌렀습니다.'}, status=status.HTTP_400_BAD_REQUEST)
                
                reaction, created = MetaReaction.objects.get_or_create(user=user, lol_meta=meta_instance)            
                
                if action == True:
                    reaction.is_like = True
                elif action == False:
                    reaction.is_like = False

                reaction.save()

                if action == True:
                    meta_instance.like_count += 1
                elif action == False:
                    meta_instance.dislike_count += 1

                meta_instance.save()

                return Response({'resultcode': 'SUCCESS', 'data': {'likes': meta_instance.like_count, 'dislikes': meta_instance.dislike_count}}, status=status.HTTP_200_OK)
            
            return Response({'resultcode': 'FAIL', 'message': '해당하는 메타가 없습니다'}, status=status.HTTP_404_NOT_FOUND)


# 리액션 삭제
class DeleteReactionView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    def delete(self, request):
        meta_id = request.data['id']
        user = request.user

        if meta_id:
            meta_instance = LolMeta.objects.get(id=meta_id)
            if meta_instance:
                meta_reaction = MetaReaction.objects.filter(user=user, lol_meta=meta_instance)
                if len(meta_reaction) > 0:

                    if meta_reaction[0].is_like == True:
                        meta_instance.like_count -= 1
                    elif meta_reaction[0].is_like == False:
                        meta_instance.dislike_count -= 1
                    meta_instance.save()
                    
                    meta_reaction.delete()

                    return Response({'resultcode': 'SUCCESS', 'data': {'likes': meta_instance.like_count, 'dislikes': meta_instance.dislike_count}}, status=status.HTTP_200_OK)

                return Response({'resultcode': 'FAIL', 'message': '리액션한 메타가 없습니다'}, status=status.HTTP_404_NOT_FOUND)

            return Response({'resultcode': 'FAIL', 'message': '해당하는 메타가 없습니다'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({'resultcode': 'FAIL', 'message': '잘못된 접근입니다.'}, status=status.HTTP_400_BAD_REQUEST)


# 댓글 조회
class CheckCommentView(APIView):
    def get(self, request):
        comment_id = request.query_params.get('comment_id')
        meta_id = request.query_params.get('meta_id')
        user_id = request.query_params.get('user_id')
        
        filter_conditions = {}
        if comment_id:
            filter_conditions['id'] = comment_id
        if meta_id:
            filter_conditions['lol_meta'] = meta_id
        if user_id:
            filter_conditions['writer'] = user_id

        comments = Comment.objects.filter(**filter_conditions)

        if comments.exists():
            serializer = CommentSerializer(comments, many=True)
            return Response({'resultcode': 'SUCCESS', 'data': serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL', 'message': '해당하는 댓글이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


# 댓글 작성
class WriteCommentView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]

    def post(self, request):
        meta_id = request.data['id']
        content = request.data['content']
        writer = request.user

        try:
            lol_meta = LolMeta.objects.get(id=meta_id)
        except:
            return Response({'resultcode': 'FAIL', 'message': '해당하는 메타가 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        data = {'meta': lol_meta.title,
                'writer': writer.nickname,
                'content': content,
                'created_at': timezone.now()}

        if lol_meta:
            Comment.objects.create(lol_meta=lol_meta, writer=writer, content=content)
            return Response({'resultcode': 'SUCCESS', 'message': '댓글 작성이 완료되었습니다.', 'data': data},status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL', 'message': '잘못된 접근입니다.'}, status=status.HTTP_400_BAD_REQUEST)


# 댓글 수정
class UpdateCommentView(APIView):
    permission_classes = [IsAuthenticatedAndTokenVerified]
    def patch(self, request):
        user = request.user
        comment_id = request.data['id']
        content = request.data['content']

        try:
            comment = Comment.objects.get(id=comment_id)
        except:
            return Response({'resultcode': 'FAIL', 'message': '해당하는 댓글이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        data = {'meta': comment.lol_meta.title,
                'writer': comment.writer.nickname,
                'content': content,
                'created_at': timezone.now()}
        
        if comment.writer == user:
            comment.content = content
            comment.created_at = timezone.now()
            comment.save()
            return Response({'resultcode': 'SUCCESS', 'message': '댓글 수정이 완료되었습니다.', 'data': data},status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL', 'message': '잘못된 접근입니다.'}, status=status.HTTP_400_BAD_REQUEST)


# 댓글 삭제
class DeleteCommentView(APIView):
    def delete(self,request):
        user = request.user
        comment_id = request.data['id']

        try:
            comment = Comment.objects.get(id=comment_id)
        except:
            return Response({'resultcode': 'FAIL', 'message': '해당하는 댓글이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        if comment.writer == user:
            comment.delete()
            return Response({'resultcode': 'SUCCESS', 'message': '댓글 삭제가 완료되었습니다.'},status=status.HTTP_200_OK)
        
        return Response({'resultcode': 'FAIL', 'message': '잘못된 접근입니다.'}, status=status.HTTP_400_BAD_REQUEST)