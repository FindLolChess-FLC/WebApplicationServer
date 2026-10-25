"""Replace the existing Cloudinary synergy SVGs with black variants."""
import base64
from pathlib import Path
from urllib.parse import unquote, urlparse

import cloudinary
import cloudinary.api
import cloudinary.uploader
from decouple import config
from django.core.management.base import BaseCommand, CommandError

from Crawling.management.commands.upload_media_cdn import collect_assets
from Crawling.img_crawl.recolor_synergy import black_svg


XML_DECLARATION = b'<?xml version="1.0" encoding="UTF-8"?>\n'


def validate_asset(asset, public_id, cloud_name):
    url = asset.get('secure_url') or ''
    parsed = urlparse(url)
    if (asset.get('public_id') != public_id or asset.get('format') != 'svg'
            or parsed.scheme != 'https' or parsed.netloc != 'res.cloudinary.com'
            or not parsed.path.startswith(f'/{cloud_name}/image/upload/')
            or not unquote(parsed.path).endswith(f'/{public_id}.svg')
            or len(url) > 255):
        raise ValueError(f'{public_id}: Cloudinary SVG 응답이 예상과 다릅니다.')
    return url


class Command(BaseCommand):
    help = '시너지 SVG를 검정색으로 덮어쓰고 기존 DB URL을 유지합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int)

    def handle(self, *args, **options):
        if options['limit'] is not None and options['limit'] < 1:
            raise CommandError('--limit은 양수여야 합니다.')
        try:
            assets = collect_assets(('synergy',))
            if options['limit'] is not None:
                assets = assets[:options['limit']]
            prepared = []
            for _model, _pk, old_url, group, name, path in assets:
                if path.suffix.lower() != '.svg':
                    raise ValueError(f'{name}: 로컬 시너지 이미지가 SVG가 아닙니다.')
                content, changed = black_svg(Path(path).read_bytes())
                prepared.append((path, old_url, f'tft/{group}/{path.stem}', content, changed))

            cloud_name = config('CLOUDNARY_NAME')
            cloudinary.config(cloud_name=cloud_name, api_key=config('CLOUDNARY_KEY'),
                              api_secret=config('CLOUDNARY_SECRET'), secure=True)
            public_ids = [public_id for _, _, public_id, _, _ in prepared]
            response = cloudinary.api.resources_by_ids(
                public_ids, max_results=len(public_ids),
                resource_type='image', type='upload')
            remote = {asset['public_id']: asset for asset in response['resources']}
            for _path, old_url, public_id, _content, _changed in prepared:
                if public_id not in remote:
                    raise ValueError(f'{public_id}: Cloudinary에 기존 이미지가 없습니다.')
                current_url = validate_asset(remote[public_id], public_id, cloud_name)
                old_path = urlparse(old_url).path
                current_path = urlparse(current_url).path
                if (old_path.rsplit('/', 1)[-1] != current_path.rsplit('/', 1)[-1]
                        or not unquote(old_path).endswith(f'/{public_id}.svg')):
                    raise ValueError(f'{public_id}: DB URL과 업로드 자산 경로가 다릅니다.')
        except (ValueError, OSError, KeyError) as exc:
            raise CommandError(str(exc)) from exc

        pending = [entry for entry in prepared if entry[-1]]
        self.stdout.write(f'시너지 SVG {len(prepared)}개 확인; 흰색 {len(pending)}개 교체 대상')
        if options['dry_run']:
            return

        for path, old_url, public_id, content, changed in pending:
            source = 'data:image/svg+xml;base64,' + base64.b64encode(
                XML_DECLARATION + content).decode('ascii')
            result = cloudinary.uploader.upload(
                source, public_id=public_id, resource_type='image',
                overwrite=True, unique_filename=False, invalidate=True)
            validate_asset(result, public_id, cloud_name)
            temporary = path.with_suffix('.svg.part')
            temporary.write_bytes(content)
            temporary.replace(path)
            self.stdout.write(f'{public_id}: 검정색 업로드 완료; DB URL 유지')

        self.stdout.write(self.style.SUCCESS(
            f'시너지 SVG {len(pending)}개 덮어쓰기 완료 (Cloudinary 캐시 무효화 요청)'))
