"""Fill empty descriptions without trusting environment-specific database IDs."""
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from Crawling.crawl.authored_guides import board_data, board_key, name_key, read_guides
from Meta.models import LolMeta, MetaGuide


class Command(BaseCommand):
    help = '제목과 대표 배치가 일치하는 기존 메타의 빈 설명만 채웁니다.'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?',
                            default=str(settings.BASE_DIR / 'Crawling/data/meta_guides.json'))
        parser.add_argument('--dry-run', action='store_true', help='DB에 저장하지 않고 확인')

    def handle(self, *args, **options):
        entries = read_guides(options['path'])
        counts = defaultdict(int)
        with transaction.atomic():
            metas = (LolMeta.objects.select_for_update().order_by('pk')
                     .prefetch_related('lolmetachampion_set__champion',
                                       'lolmetachampion_set__item'))
            by_title = defaultdict(list)
            for meta in metas:
                by_title[name_key(meta.title)].append(meta)
            # Lock existing descriptions too; never replace source-authored text.
            guides = list(MetaGuide.objects.select_for_update().order_by('pk'))
            nonempty = {guide.meta_id for guide in guides
                        if guide.level == 0 and guide.content.strip()}
            authored = {guide.meta_id: guide for guide in guides
                        if guide.level == 0 and guide.source == 'ai'}
            for entry in entries:
                candidates = by_title.get(name_key(entry['title']), [])
                reason = None
                if not candidates:
                    reason = '덱 없음'
                elif len(candidates) != 1:
                    reason = '동일 제목 여러 개'
                else:
                    meta = candidates[0]
                    if meta.pk in nonempty:
                        reason = '기존 설명 있음'
                    elif (meta.default_level != entry['default_level']
                          or board_key(board_data(meta)) != board_key(entry['board'])):
                        reason = '대표 레벨 또는 배치·성급·아이템 다름'
                if reason:
                    counts[reason] += 1
                    self.stdout.write(f"건너뜀: {entry['title']} ({reason})")
                    continue
                if not options['dry_run']:
                    guide = authored.get(meta.pk)
                    if guide is None:
                        MetaGuide.objects.create(meta=meta, source='ai', level=0,
                                                 content=entry['content'])
                    else:
                        guide.content = entry['content']
                        guide.save(update_fields=['content'])
                nonempty.add(meta.pk)
                counts['적용'] += 1
                self.stdout.write(f"{'예정' if options['dry_run'] else '저장'}: {meta.title}")
        action = '적용 예정' if options['dry_run'] else '저장 완료'
        self.stdout.write(self.style.SUCCESS(
            f"총 {len(entries)}개; {action} {counts['적용']}개; "
            f"건너뜀 {len(entries) - counts['적용']}개"))
