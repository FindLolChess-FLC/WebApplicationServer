from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from Crawling.img_crawl.save_augment import DEFAULT_DIRECTORY, save_augment


class Command(BaseCommand):
    help = 'DB에 저장된 증강체 원본 이미지를 등급별 폴더에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--output', type=Path, default=DEFAULT_DIRECTORY)
        parser.add_argument('--timeout', type=int, default=30)
        parser.add_argument('--workers', type=int, default=8)

    def handle(self, *args, **options):
        try:
            saved = save_augment(options['output'], timeout=options['timeout'], workers=options['workers'])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f'증강체 이미지 {len(saved)}개 저장 완료: {options["output"]}'))
