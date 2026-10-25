"""Refresh source guidance without creating new meta boards or comments."""
from django.core.management.base import BaseCommand, CommandError

from Crawling.crawl.lolchess_crawling import collect_lolchess_meta
from Crawling.crawl.opgg_crawling import collect_opgg_meta
from Crawling.crawl.tactics_crawling import collect_tactics_meta
from Crawling.crawl.meta_details import SOURCES, sync_meta_details


class Command(BaseCommand):
    help = '기존 메타의 상세 설명과 레벨별 배치를 갱신합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--source', action='append', choices=SOURCES)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        collectors = {
            'lolchess': lambda: collect_lolchess_meta(include_details=True),
            'opgg': collect_opgg_meta,
            'tactics': collect_tactics_meta,
        }
        sources = []
        for source in dict.fromkeys(options['source'] or SOURCES):
            self.stdout.write(f'{source}: 상세 설명·레벨 배치 수집 시작')
            self.stdout.flush()
            try:
                records = collectors[source]()
            except Exception as exc:
                raise CommandError(f'{source} 상세 정보 수집 실패: {exc}') from exc
            sources.append((source, records))
            self.stdout.write(f'{source}: {len(records)}개 수집 완료')
        try:
            sync_meta_details(sources, dry_run=options['dry_run'], write=self.stdout.write)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
