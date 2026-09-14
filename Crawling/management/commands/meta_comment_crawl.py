"""Save source-authored deck guidance as administrator comments on existing metas."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

import requests
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from Crawling.crawl.lolchess_crawling import _NextDataParser, collect_lolchess_meta
from Crawling.crawl.opgg_crawling import collect_opgg_meta
from Crawling.crawl.tactics_crawling import collect_tactics_meta
from Crawling.models import CrawledMetaComment
from Meta.models import Comment, LolMeta, LolMetaChampion


SOURCE_LABELS = {
    'lolchess': '롤체지지 덱 설명',
    'opgg': 'OP.GG 덱 설명',
    'tactics': 'tactics.tools 덱 팁',
}


class _GuideText(HTMLParser):
    """Keep readable line breaks while removing markup from an authored guide."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self.parts.append('\n\n')
        elif tag in ('br', 'hr', 'p', 'div'):
            self.parts.append('\n')
        elif tag == 'li':
            self.parts.append('\n• ')

    def handle_endtag(self, tag):
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4'):
            self.parts.append('\n\n')
        elif tag == 'li':
            self.parts.append('\n')

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        lines = (re.sub(r'[ \t\xa0]+', ' ', line).strip()
                 for line in ''.join(self.parts).splitlines())
        result = []
        for line in lines:
            if line:
                result.append(line)
            elif result and result[-1]:
                result.append('')
        while result and not result[-1]:
            result.pop()
        return '\n'.join(result)


def guide_text(html):
    parser = _GuideText()
    parser.feed(html)
    return parser.text()


def parse_lolchess_guide(html, record):
    parser = _NextDataParser()
    parser.feed(html)
    if not parser.data:
        raise ValueError(f'{record["title"]}: 가이드 데이터를 찾지 못했습니다.')
    queries = json.loads(''.join(parser.data))['props']['pageProps']['dehydratedState']['queries']
    key = record['id']
    matches = [query for query in queries
               if query.get('queryKey', [])[:2] == ['teamBuilder', key]]
    if len(matches) != 1:
        raise ValueError(f'{record["title"]}: 가이드 ID가 일치하지 않습니다.')
    builder = matches[0]['state']['data']['teamBuilder']
    if (builder.get('name', '').strip() != record['title']
            or builder.get('season') != f'set{record["season"]}'):
        raise ValueError(f'{record["title"]}: 가이드 이름이나 시즌이 다릅니다.')
    contents = builder.get('guide', {}).get('contents') or []
    # The main deck description has the deck's title. Other tabs, such as
    # recommended augments or level-specific boards, are intentionally omitted.
    main = [part for part in contents if part.get('title', '').strip() == record['title']]
    if len(main) > 1:
        raise ValueError(f'{record["title"]}: 덱 설명 항목이 중복됩니다.')
    return guide_text(main[0].get('content') or '') if main else ''


def collect_lolchess_comments(*, timeout=30, workers=5):
    records = collect_lolchess_meta(timeout=timeout)

    def fetch(record):
        response = requests.get(record['source_url'], timeout=timeout,
                                headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return record, parse_lolchess_guide(response.text, record)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return [(record, content) for record, content in pool.map(fetch, records) if content]


def collect_opgg_comments():
    # This source currently exposes board/stat data only. Accept authored
    # descriptions if its collector starts providing them in future patches.
    return [(record, record.get('description', '').strip())
            for record in collect_opgg_meta()
            if isinstance(record.get('description'), str) and record['description'].strip()]


def collect_tactics_comments():
    # Unlike a long guide, tactics.tools currently exposes short strategy tags.
    return [(record, '\n'.join(record['tips']))
            for record in collect_tactics_meta() if record.get('tips')]


def _roster(record):
    return {''.join(slot['name'].split()) for slot in record.get('champions', [])
            if slot.get('name')}


def match_meta(record, metas, rosters):
    title = record['title'].strip()
    candidates = [meta for meta in metas if meta.title == title
                  or re.fullmatch(re.escape(title) + r' [2-9][0-9]*', meta.title)]
    source_roster = _roster(record)
    scored = []
    for meta in candidates:
        target_roster = rosters.get(meta.pk, set())
        if not source_roster or not target_roster:
            continue
        similarity = len(source_roster & target_roster) / len(source_roster | target_roster)
        if similarity >= 0.7:
            scored.append((similarity, meta.title == title, meta))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    if len(scored) > 1 and scored[0][:2] == scored[1][:2]:
        return None
    return scored[0][2] if scored else None


def select_writer(writer_id=None):
    users = get_user_model().objects.filter(is_superuser=True, is_active=True)
    if writer_id is not None:
        writer = users.filter(pk=writer_id).first()
        if writer is None:
            raise CommandError(f'ID {writer_id}인 활성 슈퍼관리자 계정이 없습니다.')
        return writer
    preferred = users.filter(nickname='admin')
    if preferred.count() == 1:
        return preferred.first()
    if users.count() == 1:
        return users.first()
    raise CommandError('슈퍼관리자 계정이 여러 개입니다. --writer-id로 댓글 작성자를 지정하세요.')


def sync_comments(writer, source, meta, content):
    """Keep one plain-text comment and collapse any old paragraph comments."""
    links = list(CrawledMetaComment.objects.select_for_update().filter(
        source=source, meta_id=meta.pk).order_by('position'))
    if [link.position for link in links] != list(range(len(links))):
        raise CommandError(f'{meta.title}: 수집 댓글 순서가 연속되지 않습니다.')
    comments = {comment.pk: comment for comment in Comment.objects.select_for_update().filter(
        pk__in=[link.comment_id for link in links])}
    for link in links:
        comment = comments.get(link.comment_id)
        if comment is None or comment.writer_id != writer.pk or comment.lol_meta_id != meta.pk:
            raise CommandError(f'{meta.title}: 수집 댓글의 소유 정보가 일치하지 않습니다.')

    legacy_prefix = f'[{SOURCE_LABELS[source]}]\n'
    legacy = Comment.objects.filter(writer=writer, lol_meta=meta,
                                    content__startswith=legacy_prefix)
    if links:
        legacy = legacy.exclude(pk__in=comments)
    created = updated = unchanged = removed = 0
    if links:
        keeper = comments[links[0].comment_id]
        removed += legacy.count()
        legacy.delete()
    else:
        keeper = legacy.order_by('pk').first()
        if keeper is not None:
            extras = legacy.exclude(pk=keeper.pk)
            removed += extras.count()
            extras.delete()
        else:
            keeper = Comment.objects.create(writer=writer, lol_meta=meta, content=content)
            created += 1
        CrawledMetaComment.objects.create(
            source=source, meta_id=meta.pk, position=0,
            comment_id=keeper.pk)

    if keeper.content != content:
        keeper.content = content
        keeper.save(update_fields=['content'])
        updated += 1
    elif not created:
        unchanged += 1

    for link in links[1:]:
        comments[link.comment_id].delete()
        link.delete()
        removed += 1
    return created, updated, unchanged, removed


class Command(BaseCommand):
    help = '세 메타 사이트의 덱 설명/팁을 기존 덱에 슈퍼관리자 댓글로 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--source', action='append', choices=SOURCE_LABELS,
                            help='선택한 출처만 수집합니다. 반복 지정할 수 있습니다.')
        parser.add_argument('--writer-id', type=int)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        collectors = {
            'lolchess': collect_lolchess_comments,
            'opgg': collect_opgg_comments,
            'tactics': collect_tactics_comments,
        }
        requested = options['source'] or list(collectors)
        collected = []
        succeeded = 0
        for source in dict.fromkeys(requested):
            self.stdout.write(f'{source}: 덱 설명/팁 수집 시작')
            self.stdout.flush()
            try:
                rows = collectors[source]()
            except Exception as exc:
                if options['source']:
                    raise CommandError(f'{source} 덱 설명 수집 실패: {exc}') from exc
                self.stderr.write(f'{source}: 수집 실패, 다른 출처 계속 진행: {exc}')
                continue
            succeeded += 1
            collected.extend((source, record, content) for record, content in rows)
            self.stdout.write(f'{source}: 덱 설명/팁 {len(rows)}개 수집')
            self.stdout.flush()
        if not succeeded:
            raise CommandError('모든 출처의 덱 설명 수집에 실패했습니다.')

        metas = list(LolMeta.objects.all())
        rosters = {meta.pk: set() for meta in metas}
        for meta_id, name in LolMetaChampion.objects.values_list('meta_id', 'champion__name'):
            rosters.setdefault(meta_id, set()).add(''.join(name.split()))

        ready, unmatched = {}, []
        for source, record, text in collected:
            meta = match_meta(record, metas, rosters)
            if meta is None:
                unmatched.append(f'{source}: {record["title"]}')
                continue
            if text.strip():
                ready[(source, meta.pk)] = (source, meta, text.strip())
        self.stdout.write(f'댓글 연결 대상 {len(ready)}개, 대응 덱 없음 {len(unmatched)}개')
        for title in unmatched:
            self.stdout.write(f'건너뜀: {title}')
        if options['dry_run'] or not ready:
            return

        if CrawledMetaComment._meta.db_table not in connection.introspection.table_names():
            raise CommandError('댓글 추적 테이블이 없습니다. python manage.py migrate Crawling을 먼저 실행하세요.')

        writer = select_writer(options['writer_id'])
        created = updated = unchanged = removed = 0
        with transaction.atomic():
            for source, meta, content in ready.values():
                counts = sync_comments(writer, source, meta, content)
                created += counts[0]
                updated += counts[1]
                unchanged += counts[2]
                removed += counts[3]
        self.stdout.write(self.style.SUCCESS(
            f'슈퍼관리자 {writer.pk} 덱 설명 댓글 생성 {created}개, 수정 {updated}개, '
            f'유지 {unchanged}개, 이전 댓글 제거 {removed}개'))
