"""Convert the opaque shapes in season synergy SVGs to black."""
from xml.etree import ElementTree


def black_svg(content):
    """Only recolor the opaque white shapes, preserving transparency."""
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError('SVG 문서를 읽지 못했습니다.') from exc
    if root.tag.rsplit('}', 1)[-1] != 'svg' or root.get('fill') != 'none':
        raise ValueError('시너지 SVG의 루트 색상이 예상과 다릅니다.')
    paths = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'path']
    if not paths or any(node.get('fill') not in ('white', 'black') for node in paths):
        raise ValueError('시너지 SVG에 예상하지 못한 path 색상이 있습니다.')
    white_count = sum(node.get('fill') == 'white' for node in paths)
    if content.count(b'fill="white"') != white_count:
        raise ValueError('시너지 SVG의 흰색 표현을 안전하게 변환할 수 없습니다.')
    return content.replace(b'fill="white"', b'fill="black"'), white_count > 0
