import json
from types import SimpleNamespace

from django.test import SimpleTestCase

from Crawling.management.commands.meta_comment_crawl import (
    guide_text, match_meta, parse_lolchess_guide,
)
from Meta.serializers import CommentSerializer


class MetaCommentCrawlTests(SimpleTestCase):
    def test_guide_description_excludes_other_tabs_and_keeps_line_breaks(self):
        record = {'id': 'guide-1', 'title': '개화 Rush 9', 'season': 18}
        builder = {
            'name': record['title'], 'season': 'set18',
            'guide': {'contents': [
                {'title': record['title'],
                 'content': '<h1>개요</h1><p>운영 팁<br>아이템 추천</p>'},
                {'title': '추천 증강체', 'content': '<p>제외할 내용</p>'},
            ]},
        }
        data = {'props': {'pageProps': {'dehydratedState': {'queries': [{
            'queryKey': ['teamBuilder', 'guide-1', 'ko'],
            'state': {'data': {'teamBuilder': builder}},
        }]}}}}
        html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps(
            data, ensure_ascii=False) + '</script>'
        self.assertEqual(parse_lolchess_guide(html, record),
                         '개요\n\n운영 팁\n아이템 추천')
        self.assertNotIn('제외할 내용', parse_lolchess_guide(html, record))

    def test_api_hides_crawler_marker_and_preserves_paragraphs(self):
        comment = SimpleNamespace(
            writer=SimpleNamespace(is_superuser=True),
            content='[롤체지지 덱 설명]\n개요\n\n운영 팁\n아이템 추천',
        )
        self.assertEqual(CommentSerializer().get_content(comment),
                         '개요\n\n운영 팁\n아이템 추천')
        comment.content = '개요\n\n운영 팁\n아이템 추천'
        self.assertEqual(CommentSerializer().get_content(comment), comment.content)
        comment.content = '[롤체지지 덱 설명]\n개요'
        comment.writer.is_superuser = False
        self.assertTrue(CommentSerializer().get_content(comment).startswith('[롤체지지'))

    def test_long_guide_is_not_truncated(self):
        self.assertEqual(len(guide_text('<p>' + '가' * 600 + '</p>')), 600)

    def test_numbered_title_uses_champion_roster(self):
        exact = SimpleNamespace(pk=1, title='덱')
        numbered = SimpleNamespace(pk=2, title='덱 2')
        record = {'title': '덱', 'champions': [
            {'name': '아리'}, {'name': '케일'}, {'name': '세트'},
        ]}
        rosters = {1: {'아리', '나르', '애쉬'}, 2: {'아리', '케일', '세트'}}
        self.assertEqual(match_meta(record, [exact, numbered], rosters), numbered)
