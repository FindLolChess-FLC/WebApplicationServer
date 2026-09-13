import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from Crawling.crawl.item_crawling import item_crawling


class Command(BaseCommand):
    help = '아이템 단독 수집. 기본은 DB 비저장, --save 지정 시 저장합니다.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument('--season', type=int, default=18)
        parser.add_argument('--save', action='store_true')
        parser.add_argument('--output', type=Path)

    def handle(self, *args, **options):
        try:
            records = item_crawling(options['season'], dry_run=not options['save'])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        if options['output']:
            options['output'].write_text(
                json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8'
            )
        mode = 'DB 저장 완료' if options['save'] else 'DB 비저장'
        self.stdout.write(
            self.style.SUCCESS(f'시즌{options["season"]} 아이템 {len(records)}개: {mode}')
        )
