"""Look up the URLs of images that were previously uploaded to Cloudinary."""
from urllib.parse import urlparse

import cloudinary
import cloudinary.api
from decouple import config


FOLDERS = {'Silver': '실버', 'Gold': '골드', 'prism': '프리즘'}
GROUPS = {'synergy': '시너지', 'item': '아이템',
          'augment': '증강', 'champion': '챔피언'}


def safe_name(name):
    return ''.join(char for char in name.replace(' ', '')
                   if char not in '<>:"/\\|?*')


def public_id_for(category, record):
    group = GROUPS[category]
    if category == 'augment':
        try:
            group += '/' + FOLDERS[record['tier']]
        except KeyError as exc:
            raise ValueError(f'{record["name"]}: 알 수 없는 증강체 등급') from exc
    name = safe_name(record['name'])
    if not name:
        raise ValueError('Cloudinary 자산 이름이 비어 있습니다.')
    return f'tft/{group}/{name}'


def resolve_existing_urls(category, records):
    """Replace source URLs with actual Admin API secure_url values; never upload."""
    if not records:
        raise ValueError(f'{category}: 조회할 이미지가 없습니다.')
    cloud_name = config('CLOUDNARY_NAME')
    cloudinary.config(cloud_name=cloud_name, api_key=config('CLOUDNARY_KEY'),
                      api_secret=config('CLOUDNARY_SECRET'), secure=True)

    public_ids = [public_id_for(category, record) for record in records]
    if len(set(public_ids)) != len(public_ids):
        raise ValueError(f'{category}: 동일한 Cloudinary public ID가 중복됩니다.')

    resources = {}
    # The Admin API accepts at most 100 public IDs per request. The public_ids
    # filter cannot match '+', and the single-resource endpoint can resolve
    # a trailing '+' to the base asset. Query by prefix and match exactly.
    bulk_ids = [public_id for public_id in public_ids if '+' not in public_id]
    for start in range(0, len(bulk_ids), 100):
        batch = bulk_ids[start:start + 100]
        response = cloudinary.api.resources_by_ids(batch, max_results=len(batch),
                                                    resource_type='image', type='upload')
        resources.update((asset['public_id'], asset) for asset in response['resources'])
    for public_id in public_ids:
        if '+' in public_id:
            response = cloudinary.api.resources(
                resource_type='image', type='upload', prefix=public_id,
                max_results=100)
            resources.update((asset['public_id'], asset)
                             for asset in response['resources']
                             if asset['public_id'] == public_id)

    missing = [public_id for public_id in public_ids if public_id not in resources]
    if missing:
        raise ValueError(f'Cloudinary에 업로드된 이미지가 없습니다 ({len(missing)}개): '
                         + ', '.join(missing[:5]))

    resolved = []
    for record, public_id in zip(records, public_ids):
        asset = resources[public_id]
        url = asset.get('secure_url') or ''
        parsed = urlparse(url)
        if (asset.get('public_id') != public_id or parsed.scheme != 'https'
                or parsed.netloc != 'res.cloudinary.com'
                or not parsed.path.startswith(f'/{cloud_name}/image/upload/')
                or len(url) > 255):
            raise ValueError(f'{public_id}: Cloudinary 이미지 조회 응답이 예상과 다릅니다.')
        resolved.append({**record, 'img_src': url})
    return resolved
