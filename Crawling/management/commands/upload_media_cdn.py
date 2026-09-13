"""Publish validated set assets to Cloudinary, then switch database image URLs."""
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader
from decouple import config
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from Meta.models import AugmenterImg, ChampionImg, ItemImg, SynergyImg


ROOT = Path('tft')
EXTENSIONS = ('.svg', '.png', '.jpg', '.webp')
FOLDERS = {'Silver': '실버', 'Gold': '골드', 'prism': '프리즘'}


def _safe_name(name):
    return ''.join(char for char in name.replace(' ', '')
                   if char not in '<>:"/\\|?*')


def _local_file(folder, name):
    stem = _safe_name(name)
    matches = [folder / f'{stem}{extension}' for extension in EXTENSIONS
               if (folder / f'{stem}{extension}').is_file()]
    if len(matches) != 1:
        raise ValueError(f'{name}: 로컬 이미지가 없거나 여러 형식으로 중복됩니다 ({folder}).')
    return matches[0]


def collect_assets(categories=('synergy', 'item', 'augment', 'champion')):
    """Resolve every DB image to one existing local file before any upload."""
    assets = []
    if 'synergy' in categories:
        for pk, name, old in SynergyImg.objects.values_list('pk', 'synergy__name', 'img_src'):
            assets.append((SynergyImg, pk, old, '시너지', name,
                           _local_file(ROOT / '시너지', name)))
    if 'item' in categories:
        for pk, name, old in ItemImg.objects.values_list('pk', 'item__name', 'img_src'):
            assets.append((ItemImg, pk, old, '아이템', name,
                           _local_file(ROOT / '아이템', name)))
    if 'augment' in categories:
        for pk, name, tier, old in AugmenterImg.objects.values_list(
                'pk', 'augmenter__name', 'augmenter__tier', 'img_src'):
            if tier not in FOLDERS:
                raise ValueError(f'{name}: 알 수 없는 증강체 등급 {tier}')
            assets.append((AugmenterImg, pk, old, f'증강/{FOLDERS[tier]}', name,
                           _local_file(ROOT / '증강' / FOLDERS[tier], name)))
    if 'champion' in categories:
        for pk, name, old in ChampionImg.objects.values_list('pk', 'champion__name', 'img_src'):
            assets.append((ChampionImg, pk, old, '챔피언', name,
                           _local_file(ROOT / '챔피언', name)))
    if not assets:
        raise ValueError('업로드할 DB 이미지가 없습니다.')
    return assets


def _upload(asset, cloud_name):
    model, pk, old, group, name, path = asset
    is_svg = path.suffix.lower() == '.svg'
    resource_type = 'image'
    public_id = f'tft/{group}/{path.stem}'
    source = str(path)
    if is_svg:
        # Cloudinary's image processor needs an XML declaration for these SVGs.
        xml = b'<?xml version="1.0" encoding="UTF-8"?>\n'
        source = 'data:image/svg+xml;base64,' + base64.b64encode(
            xml + path.read_bytes()).decode('ascii')
    upload_options = {'format': 'png'} if group == '아이템' else {}
    result = cloudinary.uploader.upload(
        source, public_id=public_id, resource_type=resource_type,
        overwrite=True, unique_filename=False, invalidate=True,
        **upload_options,
    )
    url = result.get('secure_url')
    parsed = urlparse(url or '')
    if (parsed.scheme != 'https' or parsed.netloc != 'res.cloudinary.com'
            or not parsed.path.startswith(f'/{cloud_name}/{resource_type}/upload/')
            or len(url) > 255 or result.get('public_id') != public_id):
        raise ValueError(f'{name}: Cloudinary 업로드 응답이 예상과 다릅니다.')
    return model, pk, old, url


class Command(BaseCommand):
    help = '로컬 시즌 이미지를 Cloudinary에 올린 뒤 DB URL을 갱신합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--category', choices=('all', 'synergy', 'item', 'augment', 'champion'),
                            default='all')
        parser.add_argument('--workers', type=int, default=4)
        parser.add_argument('--limit', type=int, help='업로드 대상의 첫 N개만 처리합니다.')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        workers = options['workers']
        if workers < 1 or workers > 8 or (options['limit'] is not None and options['limit'] < 1):
            raise CommandError('제한 개수는 양수, 동시 업로드 수는 1~8이어야 합니다.')
        categories = (('synergy', 'item', 'augment', 'champion')
                      if options['category'] == 'all' else (options['category'],))
        try:
            assets = collect_assets(categories)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        if options['limit'] is not None:
            assets = assets[:options['limit']]
        self.stdout.write(f'업로드 대상 로컬 이미지 {len(assets)}개 검증 완료')
        if options['dry_run']:
            return

        cloud_name = config('CLOUDNARY_NAME')
        cloudinary.config(cloud_name=cloud_name, api_key=config('CLOUDNARY_KEY'),
                          api_secret=config('CLOUDNARY_SECRET'), secure=True)
        uploaded = []
        failures = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_upload, asset, cloud_name): asset
                       for asset in assets}
            for future in as_completed(futures):
                try:
                    uploaded.append(future.result())
                except Exception as exc:
                    asset = futures[future]
                    failures.append(f'{asset[4]}: {exc}')
                if (len(uploaded) + len(failures)) % 25 == 0:
                    self.stdout.write(f'Cloudinary 처리 {len(uploaded) + len(failures)}/{len(assets)}')
        if failures:
            raise CommandError(f'업로드 실패 {len(failures)}개; DB URL은 변경하지 않았습니다. '
                               + '; '.join(failures[:5]))

        with transaction.atomic():
            for model, pk, old, url in uploaded:
                if model.objects.filter(pk=pk, img_src=old).update(img_src=url) != 1:
                    raise CommandError(f'{model.__name__} {pk}: 업로드 중 DB URL이 변경됐습니다.')
        self.stdout.write(self.style.SUCCESS(f'Cloudinary {len(uploaded)}개 업로드 및 DB URL 갱신 완료'))
