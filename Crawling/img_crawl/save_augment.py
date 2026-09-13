"""Download augment images already referenced by the database."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from Crawling.img_crawl.save_item import _image_content


DEFAULT_DIRECTORY = Path('tft') / '증강'
TIER_FOLDERS = {'Silver': '실버', 'Gold': '골드', 'prism': '프리즘'}


def save_augment_img(tier, name, img_src, save_directory=DEFAULT_DIRECTORY, *, timeout=30):
    folder = TIER_FOLDERS.get(tier)
    if folder is None:
        raise ValueError(f'{name}: 알 수 없는 증강체 등급 {tier}')
    safe_name = ''.join(char for char in name if char not in '<>:"/\\|?*')
    if not safe_name:
        raise ValueError('저장할 증강체 이름이 비어 있습니다.')
    response = requests.get(img_src, timeout=timeout)
    extension, content = _image_content(response, name)
    directory = Path(save_directory) / folder
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{safe_name}{extension}'
    temporary = path.with_suffix(extension + '.part')
    temporary.write_bytes(content)
    temporary.replace(path)
    return path


def save_augment(save_directory=DEFAULT_DIRECTORY, *, timeout=30, workers=8):
    from Meta.models import AugmenterImg

    rows = list(AugmenterImg.objects.select_related('augmenter')
                .order_by('augmenter__tier', 'augmenter__name')
                .values_list('augmenter__tier', 'augmenter__name', 'img_src'))
    if not rows:
        raise ValueError('DB에 저장된 증강체 이미지 URL이 없습니다.')
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(save_augment_img, tier, name, url,
                                   save_directory, timeout=timeout)
                   for tier, name, url in rows]
        return [future.result() for future in futures]
