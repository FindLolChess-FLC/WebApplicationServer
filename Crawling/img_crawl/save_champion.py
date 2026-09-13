"""Download champion portraits referenced by the database."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from Crawling.img_crawl.save_item import _image_content


DEFAULT_DIRECTORY = Path('tft') / '챔피언'


def save_champion_img(name, img_src, save_directory=DEFAULT_DIRECTORY, *, timeout=30):
    safe_name = ''.join(char for char in name if char not in '<>:"/\\|?*')
    if not safe_name:
        raise ValueError('저장할 챔피언 이름이 비어 있습니다.')
    response = requests.get(img_src, timeout=timeout)
    extension, content = _image_content(response, name)
    directory = Path(save_directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{safe_name}{extension}'
    temporary = path.with_suffix(extension + '.part')
    temporary.write_bytes(content)
    temporary.replace(path)
    return path


def save_champion(save_directory=DEFAULT_DIRECTORY, *, timeout=30, workers=8):
    from Meta.models import ChampionImg

    rows = list(ChampionImg.objects.select_related('champion')
                .order_by('champion__name')
                .values_list('champion__name', 'img_src'))
    if not rows:
        raise ValueError('DB에 저장된 챔피언 이미지 URL이 없습니다.')
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(save_champion_img, name, url,
                                   save_directory, timeout=timeout) for name, url in rows]
        return [future.result() for future in futures]
