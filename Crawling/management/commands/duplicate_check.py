from django.core.management.base import BaseCommand
from Crawling.data_update.check_duplicate import find_duplicate_lolmeta
from Meta.models import LolMeta


class Command(BaseCommand):

    def handle(self, *args, **options):
        dupes = find_duplicate_lolmeta()

        deleted_count = 0

        for _, meta_ids in dupes.items():
            # 첫 번째 메타는 남기고 나머지를 삭제
            for meta_id in meta_ids[1:]:
                try:
                    meta = LolMeta.objects.get(id=meta_id)
                    title = meta.title
                    meta.delete()
                    self.stdout.write(self.style.SUCCESS(f'✅ 삭제됨: "{title}" (ID: {meta_id})'))
                    deleted_count += 1
                except LolMeta.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'⚠️ 존재하지 않음: LolMeta ID {meta_id}'))

        if deleted_count == 0:
            self.stdout.write(self.style.WARNING('🚫 삭제할 중복 메타가 없습니다.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'🧹 총 {deleted_count}개의 중복 메타가 삭제되었습니다.'))