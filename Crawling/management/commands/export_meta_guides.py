"""Export authored descriptions with portable board identities."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from Crawling.crawl.authored_guides import FORMAT, board_data
from Meta.models import MetaGuide


class Command(BaseCommand):
    help = '직접 작성한 메타 설명을 DB ID 없이 내보냅니다.'

    def add_arguments(self, parser):
        parser.add_argument('path', help='내보낼 JSON 파일 경로')

    def handle(self, *args, **options):
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
        path = Path(options['path'])
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
                            encoding='utf-8')
        except OSError as exc:
            raise CommandError(f'설명 파일 저장 실패: {exc}') from exc
        self.stdout.write(self.style.SUCCESS(f'{len(entries)}개 설명 내보내기 완료: {path}'))
