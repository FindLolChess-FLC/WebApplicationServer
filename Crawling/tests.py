"""DB-free regression tests: python -m unittest Crawling.tests -v."""
import unittest
import json
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import TimeoutException

from Crawling.crawl import synergy_crawling as crawler
from Crawling.crawl import item_crawling as item_crawler
from Crawling.crawl import augmenter_crawling as augment_crawler
from Crawling.crawl import champ_crawling as champion_crawler
from Crawling.crawl import browser as crawl_browser
from Crawling.img_crawl import save_item as item_images
from Crawling.crawl.lolchess_crawling import parse_lolchess_meta
from Crawling.utils import jacaard_similarity, remove_duplicates_data, similar_meta_champions


class BrowserTests(unittest.TestCase):
    @patch.object(crawl_browser, '_is_linux', return_value=True)
    @patch.object(crawl_browser.Path, 'is_file', return_value=True)
    @patch.object(crawl_browser.webdriver, 'Firefox')
    @patch.object(crawl_browser.webdriver, 'Chrome')
    def test_linux_uses_original_headless_firefox_even_with_chromedriver(
            self, chrome, firefox, _files, _linux):
        with patch.dict(crawl_browser.os.environ,
                        {'CHROME_BIN': '/snap/bin/chromium',
                         'CHROMEDRIVER_PATH': '/snap/bin/chromium.chromedriver'}):
            crawl_browser.create_driver(crawl_browser.webdriver.ChromeOptions(),
                                        firefox_user_agent='test-agent')
        options = firefox.call_args.kwargs['options']
        self.assertEqual(options.binary_location, '/usr/bin/firefox')
        self.assertIn('--headless', options.arguments)
        self.assertEqual(options.page_load_strategy, 'eager')
        self.assertEqual(options.preferences['intl.accept_languages'], 'ko,ko-KR,ko-kr')
        self.assertEqual(options.preferences['general.useragent.override'], 'test-agent')
        self.assertEqual(firefox.call_args.kwargs['service'].path,
                         '/usr/local/bin/geckodriver')
        firefox.return_value.set_window_size.assert_called_once_with(1440, 900)
        chrome.assert_not_called()

    @patch.object(crawl_browser, '_is_linux', return_value=True)
    @patch.object(crawl_browser.Path, 'is_file', return_value=False)
    @patch.object(crawl_browser.webdriver, 'Chrome')
    def test_linux_missing_firefox_fails_without_chrome_fallback(self, chrome, _files, _linux):
        with self.assertRaisesRegex(RuntimeError, 'GECKODRIVER_PATH'):
            crawl_browser.create_driver(crawl_browser.webdriver.ChromeOptions())
        chrome.assert_not_called()


def card(name='개화', **changes):
    return {'name': name, 'effect': '효과 설명',
            'img_src': 'https://cdn.lolchess.gg/trait.svg', **changes}


class SynergyTests(unittest.TestCase):
    def test_navigation_timeout_uses_loaded_synergy_dom(self):
        driver = MagicMock()
        driver.get.side_effect = TimeoutException('secondary resource timed out')
        driver.find_elements.return_value = ['trait']
        self.assertEqual(crawler._navigate_to_synergies(
            driver, 'https://lolchess.gg/synergies/set18/guide', 'div.header > h4', 0),
            ['trait'])
        driver.get.assert_called_once()

    def test_empty_synergy_page_retries_once(self):
        driver = MagicMock()
        driver.find_elements.side_effect = [[], ['trait']]
        self.assertEqual(crawler._navigate_to_synergies(
            driver, 'https://lolchess.gg/synergies/set18/guide', 'div.header > h4', 0),
            ['trait'])
        self.assertEqual(driver.get.call_count, 2)

    def test_order_by_count_preserves_repeated_tier(self):
        rows = [{'label': '11 개화', 'tier': 'chromatic'},
                {'label': '7 개화', 'tier': 'gold'},
                {'label': '3 개화', 'tier': 'bronze'},
                {'label': '5 개화', 'tier': 'gold'}]
        self.assertEqual(crawler.build_records([card()], rows)[0]['sequence'],
                         ['bronze', 'gold', 'gold', 'prism'])

    def test_one_unit_is_not_always_unique(self):
        rows = [{'label': '1 치명적인 꽃', 'tier': 'bronze'},
                {'label': '2 치명적인 꽃', 'tier': 'gold'}]
        result = crawler.build_records([card('치명적인 꽃')], rows)[0]
        self.assertEqual(result['name'], '치명적인꽃')
        self.assertEqual(result['sequence'], ['bronze', 'gold'])

    def test_missing_stats_keeps_guide_trait(self):
        with self.assertWarnsRegex(UserWarning, '일월식'):
            result = crawler.build_records([card(), card('일월식')],
                                          [{'label': '3 개화', 'tier': 'bronze'}])
        self.assertEqual(result[1]['sequence'], [])

    def test_duplicate_cards_rejected(self):
        with self.assertRaisesRegex(ValueError, '중복'):
            crawler.build_records([card(), card()], [{'label': '3 개화', 'tier': 'bronze'}])

    def test_missing_description_and_oversize_not_silently_saved(self):
        for effect in (None, '', 'a' * 501):
            with self.subTest(effect_length=len(effect or '')):
                with self.assertRaises(ValueError):
                    crawler.build_records([card(effect=effect)],
                                          [{'label': '3 개화', 'tier': 'bronze'}])

    def test_invalid_image_rejected(self):
        with self.assertRaises(ValueError):
            crawler.build_records([card(img_src='empty')],
                                  [{'label': '3 개화', 'tier': 'bronze'}])

    def test_empty_or_unknown_statistics_rejected(self):
        for rows in ([], [{'label': '3 개화', 'tier': None}],
                     [{'label': '3 미지', 'tier': 'gold'}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                crawler.build_records([card()], rows)

    def test_conflicting_tiers_rejected(self):
        with self.assertRaises(ValueError):
            crawler.build_records([card()], [{'label': '3 개화', 'tier': 'gold'},
                                            {'label': '3 개화', 'tier': 'bronze'}])

    @patch.object(crawler, 'save_synergies')
    @patch.object(crawler, 'collect_synergies', return_value=[{'name': '개화'}])
    def test_dry_run_never_calls_storage(self, collect, save):
        self.assertEqual(crawler.synergy_crawling(dry_run=True), [{'name': '개화'}])
        save.assert_not_called()

    @patch.object(crawler.webdriver, 'Chrome')
    def test_browser_closed_on_load_failure(self, chrome):
        chrome.return_value.get.side_effect = RuntimeError('load failed')
        with self.assertRaisesRegex(RuntimeError, 'load failed'):
            crawler.collect_synergies()
        chrome.return_value.quit.assert_called_once()

    @patch.object(crawler.webdriver, 'Chrome')
    def test_wrong_season_rejected_and_browser_closed(self, chrome):
        heading = MagicMock()
        heading.text = '시즌 15 시너지'
        chrome.return_value.find_elements.return_value = [heading]
        with self.assertRaisesRegex(ValueError, '시즌18'):
            crawler.collect_synergies()
        chrome.return_value.execute_script.assert_not_called()
        chrome.return_value.quit.assert_called_once()

    @patch('Crawling.management.commands.synergy_crawl.synergy_crawling', return_value=[])
    def test_command_defaults_to_no_database_write(self, crawl):
        from io import StringIO
        from Crawling.management.commands.synergy_crawl import Command
        command = Command(stdout=StringIO())
        parser = command.create_parser('manage.py', 'synergy_crawl')
        options = vars(parser.parse_args([]))
        command.handle(**options)
        crawl.assert_called_once_with(18, dry_run=True)


class ItemTests(unittest.TestCase):
    def components(self):
        return [
            {
                'name': f'재료 {index}',
                'effect': '능력치 증가',
                'img_src': f'https://cdn.example.com/component-{index}.png',
                'recipe_srcs': [],
            }
            for index in range(10)
        ]

    def test_recipe_urls_are_resolved_to_component_names(self):
        components = self.components()
        cards = [{
            'name': '완성 아이템',
            'effect': '완성 효과',
            'img_src': 'https://cdn.example.com/item.png',
            'recipe_srcs': [components[0]['img_src'], components[1]['img_src']],
        }]
        record = item_crawler.build_records(cards, components)[0]
        self.assertEqual((record['item1'], record['item2']), ('재료 0', '재료 1'))

    def test_duplicate_prefers_compatible_detailed_description(self):
        components = self.components()
        common = {
            'name': '상징',
            'img_src': 'https://cdn.example.com/emblem.png',
            'recipe_srcs': [],
        }
        cards = [
            {**common, 'effect': '특성 획득.'},
            {**common, 'effect': '특성 획득. 효과 50% 증가'},
        ]
        result = item_crawler.build_records(cards, components)
        self.assertEqual(result[0]['effect'], '특성 획득. 효과 50% 증가')
        self.assertEqual(len(result), 11)

    def test_image_signature_wins_over_incorrect_content_type(self):
        response = MagicMock()
        response.content = b'\xff\xd8\xff' + b'jpeg data'
        response.headers = {'content-type': 'image/png'}
        extension, content = item_images._image_content(response, 'B.F. 대검')
        self.assertEqual(extension, '.jpg')
        self.assertEqual(content, response.content)


class AugmentTests(unittest.TestCase):
    def test_visible_augments_preserve_distinct_variants(self):
        image_a = 'https://cdn.example.com/a.png'
        image_b = 'https://cdn.example.com/b.png'
        source = [
            {'key': 'Flower', 'name': '꽃', 'desc': '효과<br>하나',
             'imageUrl': image_a, 'tier': 2},
            {'key': 'FlowerPlus', 'name': '꽃', 'desc': '효과 둘',
             'imageUrl': image_b, 'tier': 2},
            {'key': 'Hidden', 'name': '숨김', 'desc': '효과',
             'imageUrl': 'https://cdn.example.com/hidden.png',
             'tier': 1, 'isHidden': True},
        ]
        shown = [{'name': '꽃', 'img_src': image_a},
                 {'name': '꽃', 'img_src': image_b}]
        records = augment_crawler.build_records(source, shown)
        self.assertEqual([row['name'] for row in records], ['꽃', '꽃+'])
        self.assertEqual(records[0]['effect'], '효과 하나')
        self.assertTrue(all(row['tier'] == 'Gold' for row in records))

    def test_displayed_augment_must_match_page_data(self):
        with self.assertRaises(ValueError):
            augment_crawler.build_records(
                [{'name': '꽃', 'desc': '효과', 'imageUrl': 'https://cdn.example.com/a.png', 'tier': 2}],
                [{'name': '다른 이름', 'img_src': 'https://cdn.example.com/a.png'}],
            )


class ChampionTests(unittest.TestCase):
    def test_public_champion_maps_first_cost_and_trait_name(self):
        image = 'https://cdn.example.com/rakan.jpg'
        champions = [
            {'name': '라 칸', 'cost': [1, 3, 9], 'traits': ['Fae', 'Vanguard'],
             'imageUrl': image},
            {'name': '숨김', 'cost': [5, 14, 44], 'traits': ['Fae'],
             'imageUrl': 'https://cdn.example.com/hidden.jpg', 'isHidden': True},
        ]
        traits = [{'key': 'Fae', 'name': '요 정'},
                  {'key': 'Vanguard', 'name': '선봉대'}]
        result = champion_crawler.build_records(champions, traits, [image])
        self.assertEqual(result, [{
            'name': '라칸', 'price': 1, 'synergies': ['요정', '선봉대'],
            'img_src': image,
        }])

    def test_page_and_source_champion_lists_must_match(self):
        with self.assertRaises(ValueError):
            champion_crawler.build_records(
                [{'name': '라칸', 'cost': [1], 'traits': ['Fae'],
                  'imageUrl': 'https://cdn.example.com/rakan.jpg'}],
                [{'key': 'Fae', 'name': '요정'}],
                ['https://cdn.example.com/other.jpg'],
            )


class LolchessMetaTests(unittest.TestCase):
    def test_hidden_zero_cost_unit_is_kept_with_source_image(self):
        champion_refs = {'season': 'set18', 'champions': [
            {'key': 'Hero', 'name': '영웅', 'cost': [1],
             'imageUrl': 'https://cdn.lolchess.gg/hero.jpg'},
            {'key': 'Summon', 'name': '소환수', 'cost': [0], 'isHidden': True,
             'imageUrl': 'https://cdn.lolchess.gg/summon.png'},
        ]}
        item_refs = {'season': 'set18', 'items': [
            {'key': 'Sword', 'name': '검'}]}
        guide = {'guideDecks': [{
            'teamBuilderKey': 'guide1', 'name': '시험 덱', 'season': 'set18',
            'data': {'set': 'set18', 'slots': [
                {'index': index, 'champion': 'Summon' if index == 0 else 'Hero',
                 'items': ['Sword'] if index == 1 else []}
                for index in range(5)]},
        }]}
        queries = [
            {'queryKey': [key], 'state': {'data': data}}
            for key, data in [('championRefs', champion_refs),
                              ('itemRefs', item_refs), ('getGuideDecks', guide)]
        ]
        html = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps({
            'props': {'pageProps': {'dehydratedState': {'queries': queries}}}
        }) + '</script>'
        record = parse_lolchess_meta(html)[0]
        self.assertEqual(len(record['champions']), 5)
        self.assertEqual(record['champions'][0]['location'], 1)
        self.assertEqual(record['champions'][0]['star'], 1)
        self.assertTrue(record['champions'][0]['is_summon'])
        self.assertEqual(record['champions'][0]['image_url'],
                         'https://cdn.lolchess.gg/summon.png')
        self.assertFalse(record['champions'][1]['is_summon'])
        self.assertEqual(record['champions'][1]['items'], ['검'])


class MetaSimilarityTests(unittest.TestCase):
    def test_one_low_cost_swap_and_extra_flex_unit_are_duplicates(self):
        prices = dict.fromkeys('ABCDEFGHI', 1)
        prices.update({'G': 4, 'H': 5})
        original = list('ABCDEFGH')
        self.assertLess(jacaard_similarity(original, list('ACDEFGHI')), 0.8)
        self.assertTrue(similar_meta_champions(original, list('ACDEFGHI'), prices))
        self.assertTrue(similar_meta_champions(original, list('ABCDEFGHI'), prices))

    def test_high_cost_carry_swap_is_distinct_even_above_jaccard_threshold(self):
        prices = dict.fromkeys('ABCDEFGHIJK', 1)
        prices.update({'J': 5, 'K': 5})
        first, second = list('ABCDEFGHIJ'), list('ABCDEFGHIK')
        self.assertGreater(jacaard_similarity(first, second), 0.8)
        self.assertFalse(similar_meta_champions(first, second, prices))

    def test_merge_keeps_first_and_never_mutates_inputs(self):
        old = {'old': {'챔프': list('ABCDEFGH')}}
        incoming = {'variant': {'챔프': list('ACDEFGHI')},
                    'different': {'챔프': list('JKLMNOPQ')}}
        prices = dict.fromkeys('ABCDEFGHIJKLMNOPQ', 1)
        result = remove_duplicates_data(old, incoming, prices=prices)
        self.assertEqual(list(result), ['old', 'different'])
        self.assertEqual(list(old), ['old'])
        self.assertEqual(list(incoming), ['variant', 'different'])
