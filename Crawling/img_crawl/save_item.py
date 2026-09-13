"""Download the item images referenced by the current database records."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests


DEFAULT_DIRECTORY = Path('tft') / '아이템'
IMAGE_SIGNATURES = (
    ('.png', b'\x89PNG\r\n\x1a\n'),
    ('.jpg', b'\xff\xd8\xff'),
    ('.webp', b'RIFF'),
)


def _image_content(response, name):
    response.raise_for_status()
    content = response.content
    for extension, signature in IMAGE_SIGNATURES:
        if content.startswith(signature):
            if extension == '.webp' and content[8:12] != b'WEBP':
                continue
            return extension, content
    media_type = response.headers.get('content-type', '').split(';', 1)[0].lower()
    raise ValueError(f'{name}: 지원하지 않는 이미지 내용입니다 ({media_type}).')


def save_item_img(name, img_src, save_directory=DEFAULT_DIRECTORY, *, timeout=30):
    directory = Path(save_directory)
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = ''.join(char for char in name.replace(' ', '') if char not in '<>:"/\\|?*')
    if not safe_name:
        raise ValueError('저장할 아이템 이름이 비어 있습니다.')
    response = requests.get(img_src, timeout=timeout)
    extension, content = _image_content(response, name)
    file_path = directory / f'{safe_name}{extension}'
    temporary_path = file_path.with_suffix(extension + '.part')
    temporary_path.write_bytes(content)
    temporary_path.replace(file_path)
    return file_path


def save_item(save_directory=DEFAULT_DIRECTORY, *, timeout=30, workers=8):
    from Meta.models import ItemImg

    image_rows = list(
        ItemImg.objects.select_related('item')
        .order_by('item__name')
        .values_list('item__name', 'img_src')
    )
    if not image_rows:
        raise ValueError('DB에 저장된 아이템 이미지 URL이 없습니다.')
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(save_item_img, name, url, save_directory, timeout=timeout)
            for name, url in image_rows
        ]
        return [future.result() for future in futures]
