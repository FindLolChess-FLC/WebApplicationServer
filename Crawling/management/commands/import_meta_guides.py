"""Fill empty descriptions without trusting environment-specific database IDs."""
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from Crawling.crawl.authored_guides import content_for_board, match_guide, name_key, read_guides
from Meta.models import Champion, LolMeta, MetaGuide


class Command(BaseCommand):
    help = '주력 유닛·상징·리롤 목표가 같은 기존 메타의 빈 설명을 채웁니다.'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?',
                            default=str(settings.BASE_DIR / 'Crawling/data/meta_guides.json'))
        parser.add_argument('--dry-run', action='store_true', help='DB에 저장하지 않고 확인')
        parser.add_argument('--strict', action='store_true', help='이전 방식대로 제목·대표 배치 완전 일치만 허용')

    def handle(self, *args, **options):
        entries = read_guides(options['path'])
        counts = Counter()
        prices = {name_key(name): cost for name, cost in Champion.objects.values_list('name', 'price')}
        with transaction.atomic():
            metas = list(LolMeta.objects.select_for_update().order_by('pk')
                     .prefetch_related('lolmetachampion_set__champion',
                                       'lolmetachampion_set__item'))
            # Lock existing descriptions too; never replace source-authored text.
            guides = list(MetaGuide.objects.select_for_update().order_by('pk'))
            nonempty = {guide.meta_id for guide in guides
                        if guide.level == 0 and guide.content.strip()}
            authored = {guide.meta_id: guide for guide in guides
                        if guide.level == 0 and guide.source == 'ai'}
            for meta in metas:
                if meta.pk in nonempty:
                    counts['기존 설명 있음'] += 1
                    self.stdout.write(f'건너뜀: {meta.title} (기존 설명 있음)')
                    continue
                entry, reason = match_guide(meta, entries, prices, strict=options['strict'])
                if entry is None:
                    counts[reason] += 1
                    self.stdout.write(f'건너뜀: {meta.title} ({reason})')
                    continue
                content = entry['content'] if options['strict'] else content_for_board(entry, meta)
                if not options['dry_run']:
                    guide = authored.get(meta.pk)
                    if guide is None:
                        MetaGuide.objects.create(meta=meta, source='ai', level=0,
                                                 source_id=f"authored:{entry['title']}",
                                                 content=content)
                    else:
                        guide.content = content
                        guide.source_id = f"authored:{entry['title']}"
                        guide.save(update_fields=['content', 'source_id'])
                nonempty.add(meta.pk)
                counts['적용'] += 1
                self.stdout.write(f"{'예정' if options['dry_run'] else '저장'}: "
                                  f"{entry['title']} → {meta.title} ({reason})")
        action = '적용 예정' if options['dry_run'] else '저장 완료'
        self.stdout.write(self.style.SUCCESS(
            f"설명 원본 {len(entries)}개; DB 메타 {len(metas)}개; {action} {counts['적용']}개; "
            f"건너뜀 {len(metas) - counts['적용']}개"))
