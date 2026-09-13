from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from Crawling.img_crawl.save_synergy import DEFAULT_DIRECTORY, save_synergy


class Command(BaseCommand):
    help = 'DB에 저장된 시너지 원본 SVG를 로컬 폴더에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=Path, default=DEFAULT_DIRECTORY)
        parser.add_argument('--timeout', type=int, default=30)

    def handle(self, *args, **options):
        try:
            saved = save_synergy(options['output'], timeout=options['timeout'])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(f'시너지 SVG {len(saved)}개 저장 완료: {options["output"]}')
        )
