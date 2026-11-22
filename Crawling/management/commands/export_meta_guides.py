"""Export authored descriptions with portable board identities."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch
from django.utils import timezone

from Crawling.crawl.authored_guides import FORMAT, board_data
from Meta.models import Augmenter, Champion, Item, LolMeta, MetaGuide, Synergy


def missing_context():
    """Export public game data for unmatched boards, never user/account records."""
    metas = LolMeta.objects.order_by('pk').prefetch_related(
        Prefetch('guides', queryset=MetaGuide.objects.filter(level=0)),
        'lolmetachampion_set__champion', 'lolmetachampion_set__item')
    entries = [
        {'title': meta.title, 'default_level': meta.default_level,
         'reroll_lv': meta.reroll_lv, 'board': board_data(meta)}
        for meta in metas
        if not any(guide.content.strip() for guide in meta.guides.all())
    ]
    champion_names = {slot['name'] for entry in entries for slot in entry['board']}
    item_names = {item for entry in entries for slot in entry['board'] for item in slot['items']}
    champions = [
        {'name': champion.name, 'price': champion.price,
         'traits': [trait.name for trait in champion.synergy.all()]}
        for champion in Champion.objects.filter(name__in=champion_names)
        .prefetch_related('synergy').order_by('name')
    ]
    trait_names = {trait for champion in champions for trait in champion['traits']}
    return {
        'format': 'flc-meta-context-v1', 'created_at': timezone.now().isoformat(),
        'metas': entries, 'champions': champions,
        'items': list(Item.objects.filter(name__in=item_names).order_by('name')
                      .values('name', 'effect', 'item1', 'item2')),
        'traits': list(Synergy.objects.filter(name__in=trait_names).order_by('name')
                       .values('name', 'effect', 'sequence')),
        'augments': list(Augmenter.objects.filter(
            name__in=['저주받은 왕관', '어둠의 의식', '특성 사다리'])
            .order_by('name').values('name', 'effect')),
    }


class Command(BaseCommand):
    help = '작성 설명 또는 설명이 빈 덱의 분석 자료를 DB ID 없이 내보냅니다.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='내보낼 JSON 파일 경로')
        parser.add_argument('--missing', action='store_true',
                            help='설명이 빈 덱의 구성·아이템·특성을 분석 자료로 내보냄')

    def handle(self, *args, **options):
        if options['missing']:
            payload = missing_context()
            count = len(payload['metas'])
        else:
            guides = (MetaGuide.objects.filter(source='ai', level=0).exclude(content='')
                      .select_related('meta').prefetch_related(
                          'meta__lolmetachampion_set__champion',
                          'meta__lolmetachampion_set__item').order_by('meta_id'))
            entries = [
                {'title': guide.meta.title, 'default_level': guide.meta.default_level,
                 'board': board_data(guide.meta), 'content': guide.content}
                for guide in guides if guide.content.strip()
            ]
            if not entries:
                raise CommandError('내보낼 작성 설명이 없습니다.')
            payload = {'format': FORMAT, 'created_at': timezone.now().isoformat(),
                       'guides': entries}
            count = len(entries)
        path = Path(options['path'])
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
                            encoding='utf-8')
        except OSError as exc:
            raise CommandError(f'설명 파일 저장 실패: {exc}') from exc
        label = '빈 설명 덱 분석 자료' if options['missing'] else '작성 설명'
        self.stdout.write(self.style.SUCCESS(f'{label} {count}개 내보내기 완료: {path}'))
