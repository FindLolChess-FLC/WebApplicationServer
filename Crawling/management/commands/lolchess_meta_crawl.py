"""Validate and save set-specific recommended comps from lolchess.gg only."""
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

import cloudinary
import cloudinary.uploader
import requests
from decouple import config

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from Crawling.crawl.lolchess_crawling import collect_lolchess_meta
from Crawling.utils import reroll_lv
from Meta.models import Champion, ChampionImg, Item, LolMeta, LolMetaChampion


def _key(name):
    return ''.join(name.split())


def summoned_units(records):
    units = {}
    for record in records:
        for slot in record['champions']:
            if not slot['is_summon']:
                continue
            name = slot['name']
            url = slot['image_url']
            parsed = urlparse(url)
            if (parsed.scheme != 'https' or parsed.netloc != 'cdn.lolchess.gg'
                    or not parsed.path.endswith('.png')):
                raise ValueError(f'{name}: 소환 유닛 이미지 주소가 예상과 다릅니다.')
            if name in units and units[name] != url:
                raise ValueError(f'{name}: 소환 유닛 이미지 주소가 중복 배치에서 다릅니다.')
            units[name] = url
    return units


def resolve_references(records):
    champions = {_key(champion.name): champion for champion in Champion.objects.all()}
    items = {_key(item.name): item for item in Item.objects.all()}
    wanted_champions = {slot['name'] for record in records for slot in record['champions']}
    wanted_items = {name for record in records for slot in record['champions']
                    for name in slot['items']}
    missing_champions = sorted(name for name in wanted_champions
                               if _key(name) not in champions)
    missing_items = sorted(name for name in wanted_items if _key(name) not in items)
    return champions, items, missing_champions, missing_items


def upload_summoned_images(units):
    cloud_name = config('CLOUDNARY_NAME')
    cloudinary.config(cloud_name=cloud_name, api_key=config('CLOUDNARY_KEY'),
                      api_secret=config('CLOUDNARY_SECRET'), secure=True)
    folder = Path('tft/챔피언')
    folder.mkdir(parents=True, exist_ok=True)
    uploaded = {}
    for name, source_url in units.items():
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()
        if response.content.startswith(b'\x89PNG\r\n\x1a\n'):
            extension = '.png'
        elif response.content.startswith(b'\xff\xd8\xff'):
            extension = '.jpg'
        else:
            raise ValueError(f'{name}: 내려받은 소환 유닛 이미지 형식을 알 수 없습니다.')
        path = folder / f'{_key(name)}{extension}'
        path.write_bytes(response.content)
        public_id = f'tft/챔피언/{path.stem}'
        result = cloudinary.uploader.upload(
            str(path), public_id=public_id, resource_type='image',
            overwrite=True, unique_filename=False, invalidate=True)
        cdn_url = result.get('secure_url', '')
        parsed = urlparse(cdn_url)
        if (result.get('public_id') != public_id or parsed.scheme != 'https'
                or parsed.netloc != 'res.cloudinary.com'
                or not parsed.path.startswith(f'/{cloud_name}/image/upload/')
                or not unquote(parsed.path).endswith(f'/{public_id}{extension}')
                or len(cdn_url) > 255):
            raise ValueError(f'{name}: Cloudinary 이미지 응답이 예상과 다릅니다.')
        uploaded[name] = cdn_url
    return uploaded


def save_records(records, champions, items):
    with transaction.atomic():
        for record in records:
            meta, _ = LolMeta.objects.get_or_create(title=record['title'])
            LolMetaChampion.objects.filter(meta=meta).delete()
            stars_by_cost = Counter()
            for slot in record['champions']:
                champion = champions[_key(slot['name'])]
                placed = LolMetaChampion.objects.create(
                    meta=meta, champion=champion,
                    star=slot['star'], location=slot['location'])
                placed.item.set([items[_key(name)] for name in slot['items']])
                if champion.price > 0:
                    stars_by_cost[champion.price] += slot['star']
            max_stars = max(stars_by_cost.values())
            dominant_cost = max(cost for cost, stars in stars_by_cost.items()
                                if stars == max_stars)
            meta.reroll_lv = reroll_lv(dominant_cost)
            meta.save(update_fields=['reroll_lv'])


class Command(BaseCommand):
    help = 'lolchess.gg 추천 메타 덱을 검증하고 DB에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--season', type=int, default=18)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        season = options['season']
        if season < 1:
            raise CommandError('시즌은 양수여야 합니다.')
        try:
            records = collect_lolchess_meta(season=season)
        except (ValueError, KeyError, IndexError) as exc:
            raise CommandError(f'lolchess.gg 데이터 해석 실패: {exc}') from exc

        self.stdout.write(f'메타 덱 {len(records)}개, 챔피언 배치 '
                          f'{sum(len(record["champions"]) for record in records)}개 수집')
        try:
            units = summoned_units(records)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f'소환 유닛 {len(units)}종, 배치 '
                          f'{sum(slot["is_summon"] for record in records for slot in record["champions"])}개')
        champions, items, missing_champions, missing_items = resolve_references(records)
        missing_regular = sorted(set(missing_champions) - units.keys())
        self.stdout.write(f'DB에 없는 챔피언 {len(missing_champions)}개, '
                          f'아이템 {len(missing_items)}개')
        if missing_regular:
            self.stdout.write('일반 챔피언: ' + ', '.join(missing_regular))
        if missing_items:
            self.stdout.write('아이템: ' + ', '.join(missing_items))
        if missing_regular or missing_items:
            raise CommandError('참조 데이터가 부족해 DB 저장을 중단했습니다.')
        if options['dry_run']:
            self.stdout.write('일반 챔피언·아이템 참조 검증 완료; 이미지 업로드와 DB 저장은 생략했습니다.')
            return
        try:
            uploaded = upload_summoned_images(units)
        except (requests.RequestException, ValueError) as exc:
            raise CommandError(f'소환 유닛 이미지 업로드 실패: {exc}') from exc
        with transaction.atomic():
            for name, url in uploaded.items():
                champion, _ = Champion.objects.update_or_create(
                    name=_key(name), defaults={'price': 0})
                ChampionImg.objects.update_or_create(
                    champion=champion, defaults={'img_src': url})
            champions, items, missing_champions, missing_items = resolve_references(records)
            if missing_champions or missing_items:
                raise CommandError('소환 유닛 저장 후에도 DB 참조가 일치하지 않습니다.')
            save_records(records, champions, items)
        self.stdout.write(self.style.SUCCESS(
            f'소환 유닛 {len(uploaded)}종 CDN/DB 저장, 메타 덱 {len(records)}개 배치 저장 완료'))
