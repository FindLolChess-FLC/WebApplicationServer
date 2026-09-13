"""Download the synergy SVGs referenced by the current database records."""
from pathlib import Path
from xml.etree import ElementTree

import requests


DEFAULT_DIRECTORY = Path('tft') / '시너지'


def _svg_content(response, name):
    response.raise_for_status()
    content = response.content
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError(f'{name}: 응답이 올바른 SVG가 아닙니다.') from exc
    if root.tag.rsplit('}', 1)[-1].lower() != 'svg':
        raise ValueError(f'{name}: 응답의 루트 요소가 SVG가 아닙니다.')
    return content


def save_synergy_img(name, img_src, save_directory=DEFAULT_DIRECTORY, *, timeout=30, session=None):
    """Download one SVG and replace the destination only after validation."""
    directory = Path(save_directory)
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = ''.join(char for char in name.replace(' ', '') if char not in '<>:"/\\|?*')
    if not safe_name:
        raise ValueError('저장할 시너지 이름이 비어 있습니다.')

    client = session or requests
    response = client.get(img_src, timeout=timeout)
    content = _svg_content(response, name)
    file_path = directory / f'{safe_name}.svg'
    temporary_path = file_path.with_suffix('.svg.part')
    temporary_path.write_bytes(content)
    temporary_path.replace(file_path)
    return file_path


def save_synergy(save_directory=DEFAULT_DIRECTORY, *, timeout=30):
    """Download every distinct synergy image currently stored in the database."""
    from Meta.models import SynergyImg

    image_rows = list(
        SynergyImg.objects.select_related('synergy')
        .order_by('synergy__name')
        .values_list('synergy__name', 'img_src')
    )
    if not image_rows:
        raise ValueError('DB에 저장된 시너지 이미지 URL이 없습니다.')

    saved = []
    with requests.Session() as session:
        for name, img_src in image_rows:
            saved.append(
                save_synergy_img(
                    name, img_src, save_directory, timeout=timeout, session=session
                )
            )
    return saved
