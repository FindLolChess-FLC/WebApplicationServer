"""Portable, data-only descriptions matched against an existing meta board."""
import json
from pathlib import Path

from django.core.management.base import CommandError


FORMAT = 'flc-meta-guides-v1'


def name_key(value):
    return ''.join(value.split())


def board_data(meta):
    return sorted([
        {'name': placed.champion.name, 'star': placed.star,
         'location': placed.location,
         'items': sorted(item.name for item in placed.item.all())}
        for placed in meta.lolmetachampion_set.all()
    ], key=lambda slot: slot['location'])


def board_key(board):
    return sorted((name_key(slot['name']), slot['star'], slot['location'],
                   tuple(sorted(name_key(item) for item in slot['items'])))
                  for slot in board)


def read_guides(path):
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if payload.get('format') != FORMAT or not isinstance(payload.get('guides'), list):
            raise ValueError('지원하지 않는 설명 파일 형식입니다.')
        entries = payload['guides']
        seen = set()
        for entry in entries:
            title, content = entry['title'], entry['content']
            if (not isinstance(title, str) or not title.strip()
                    or not isinstance(content, str) or not content.strip()
                    or len(content) > 20000 or '\x00' in content):
                raise ValueError('제목 또는 설명이 올바르지 않습니다.')
            level = entry['default_level']
            if type(level) is not int or not 1 <= level <= 10:
                raise ValueError(f'{title}: 대표 레벨이 올바르지 않습니다.')
            if not isinstance(entry['board'], list) or not entry['board']:
                raise ValueError(f'{title}: 배치 정보가 비어 있습니다.')
            locations = set()
            for slot in entry['board']:
                if (not isinstance(slot['name'], str) or not slot['name'].strip()
                        or type(slot['star']) is not int or not 1 <= slot['star'] <= 3
                        or type(slot['location']) is not int or not 1 <= slot['location'] <= 28
                        or slot['location'] in locations
                        or not isinstance(slot['items'], list) or len(slot['items']) > 3
                        or any(not isinstance(item, str) or not item.strip()
                               for item in slot['items'])):
                    raise ValueError(f'{title}: 배치 정보가 올바르지 않습니다.')
                locations.add(slot['location'])
            identity = name_key(title)
            if identity in seen:
                raise ValueError(f'{title}: 중복된 제목입니다.')
            seen.add(identity)
        return entries
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise CommandError(f'설명 파일을 읽지 못했습니다: {exc}') from exc
