"""Browser-level regression tests for the standalone mobile app.

Run: python3 tests/test_app.py
Requires Python Playwright and an installed Chromium (no npm/build step).
"""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import shutil
import threading
import unittest

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / '.test-results'
KEY = 'little-basket:v1'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class BasketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/little-basket.html'
        cls.playwright = sync_playwright().start()
        executable = os.environ.get('BASKET_CHROMIUM') or shutil.which('chromium')
        cls.browser = cls.playwright.chromium.launch(
            executable_path=executable, args=['--no-sandbox'])
        RESULTS.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.goto(self.url)
        self.tab('recipes')

    def tearDown(self):
        self.assertEqual(self.errors, [], 'Unexpected JavaScript runtime error')
        self.context.close()

    def tab(self, name):
        nav = '.mobile-nav' if self.page.viewport_size['width'] <= 760 else '.desktop-tabs'
        self.page.locator(f'{nav} [data-view="{name}"]').click()

    def select(self, recipe):
        self.page.locator(f'[data-recipe="{recipe}"] .recipe-add').click()

    def saved(self):
        return self.page.evaluate('(k)=>JSON.parse(localStorage.getItem(k))', KEY)

    def test_01_initial_recipes_and_no_assumed_inventory(self):
        self.assertEqual(self.page.locator('.recipe-card').count(), 11)
        self.assertEqual(self.saved()['stock'], [])
        self.assertNotIn('山药', self.page.locator('#recipes-view').inner_text())
        self.assertIn('清炒薯苗', self.page.locator('#recipe-grid').inner_text())
        self.tab('shopping')
        self.assertTrue(self.page.get_by_text('菜篮子还空着', exact=True).is_visible())

    def test_02_shared_ingredients_merge_and_scale(self):
        self.select('tomato-soup')
        self.select('potato-mince')
        self.tab('shopping')
        row = self.page.locator('[data-grocery="potato"]')
        self.assertEqual(row.count(), 1)
        self.assertEqual(row.locator('.grocery-qty').inner_text(), '3 个')
        self.assertIn('番茄马铃薯排骨汤、马铃薯肉碎', row.inner_text())
        self.page.get_by_label('清单增加一人', exact=True).click()
        self.assertEqual(self.page.locator('[data-grocery="potato"] .grocery-qty').inner_text(), '4.5 个')

    def test_03_soup_bones_are_one_identity(self):
        self.select('tomato-soup')
        self.select('lotus-soup')
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="bones"]').count(), 1)
        self.assertEqual(self.page.locator('[data-grocery="bones"] .grocery-qty').inner_text(), '1,000 g')
        self.page.get_by_role('button', name='加一样', exact=True).click()
        self.page.locator('#item-name').fill('猪骨')
        self.page.locator('#item-qty').fill('请老板斩小块')
        self.page.locator('#item-form button[type="submit"]').click()
        self.assertEqual(self.page.locator('[data-grocery="bones"]').count(), 1)
        self.assertIn('请老板斩小块', self.page.locator('[data-grocery="bones"]').inner_text())

    def test_04_purchase_progress_survives_reload_and_quantity_change(self):
        self.select('tomato-soup')
        self.tab('shopping')
        self.page.locator('[data-grocery="tomato"] .purchase-check').click()
        self.assertIn('tomato', self.saved()['checked'])
        self.page.reload()
        self.assertTrue(self.page.locator('#shopping-view').is_visible())
        self.assertEqual(self.page.locator('[data-grocery="tomato"] .purchase-check').get_attribute('aria-checked'), 'true')
        self.page.get_by_label('清单增加一人', exact=True).click()
        self.assertNotIn('tomato', self.saved()['checked'])

    def test_05_pantry_exclusion_and_replenishment(self):
        self.select('tomato-egg')
        self.tab('pantry')
        self.page.locator('[data-kitchen="fresh"]').click()
        self.page.locator('[data-pantry-id="egg"] .stock-toggle').click()
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="egg"]').count(), 0)
        self.page.locator('.stock-excluded summary').click()
        self.assertIn('鸡蛋', self.page.locator('.stock-excluded').inner_text())
        self.tab('pantry')
        self.page.locator('[data-pantry-id="egg"] .replenish').click()
        self.page.locator('#reminder-items input[value="egg"]').check()
        self.page.locator('#reminder-continue').click()
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="egg"]').count(), 1)
        self.assertNotIn('egg', self.saved()['stock'])

    def test_06_pork_recipe_variants_change_shopping_list(self):
        self.select('pork-stew')
        self.page.locator('[data-recipe="pork-stew"] .art-open').click()
        self.page.locator('[data-action="variant"][data-variant="anise"]').click()
        self.assertIn('这一版不用酸梅酱', self.page.locator('#detail-body').inner_text())
        self.page.get_by_label('关闭菜谱', exact=True).click()
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="anise"]').count(), 1)
        self.assertEqual(self.page.locator('[data-grocery="plum"]').count(), 0)
        self.assertEqual(self.page.locator('[data-grocery="oyster"]').count(), 0)

    def test_07_edit_recipe_and_preserve_it_after_builtin_update(self):
        self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
        self.page.locator('[data-action="edit-recipe"]').click()
        self.page.locator('#edit-title').fill('新学的番茄豆腐')
        rows = self.page.locator('.ingredient-editor')
        rows.nth(0).locator('.ing-name').fill('西红柿')
        rows.nth(0).locator('.ing-qty').fill('2')
        rows.nth(0).locator('.ing-unit').fill('个')
        rows.nth(1).locator('.ing-name').fill('豆腐')
        rows.nth(1).locator('.ing-qty').fill('1')
        rows.nth(1).locator('.ing-unit').fill('盒')
        self.page.locator('#edit-steps').fill('番茄切块。\n豆腐下锅煮熟。')
        self.page.locator('#edit-source').fill('https://www.xiaohongshu.com/')
        self.page.locator('#edit-learning').check()
        self.page.locator('#recipe-form button[type="submit"]').click()
        self.assertEqual(self.page.locator('.recipe-card').count(), 11)
        added = self.saved()['recipes'][0]
        self.assertEqual(added['ingredients'][0]['id'], 'tomato')
        self.assertTrue(added['learning'])
        self.page.locator('[data-filter="learning"]').click()
        self.assertEqual(self.page.locator('.recipe-card').count(), 1)
        self.page.locator('.recipe-card .art-open').click()
        self.assertEqual(self.page.locator('#detail-body .steps li').count(), 2)
        self.page.locator('[data-action="edit-recipe"]').click()
        self.page.locator('#edit-title').fill('我的番茄豆腐')
        self.page.locator('#recipe-form button[type="submit"]').click()
        self.page.reload()
        self.page.locator('#recipe-search').fill('豆腐')
        self.assertEqual(self.page.locator('.recipe-card').count(), 1)
        self.assertIn('我的番茄豆腐', self.page.locator('.recipe-card').inner_text())

    def test_08_single_ingredient_recipe_and_dirty_form_cancel(self):
        self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
        self.page.locator('[data-action="edit-recipe"]').click()
        self.page.locator('#edit-title').fill('水煮鸡蛋')
        while self.page.locator('.ingredient-editor').count() > 1:
            self.page.locator('.ingredient-editor').last.locator('button').click()
        self.page.locator('.ingredient-editor').first.locator('.ing-name').fill('鸡蛋')
        self.page.get_by_label('关闭编辑', exact=True).click()
        self.assertTrue(self.page.locator('#confirm-dialog').is_visible())
        self.page.locator('#confirm-dialog [data-action="close"]').first.click()
        self.assertTrue(self.page.locator('#editor-dialog').is_visible())
        self.page.locator('#recipe-form button[type="submit"]').click()
        self.assertEqual(self.saved()['recipes'][0]['title'], '水煮鸡蛋')

    def test_09_export_import_and_malformed_backup(self):
        self.select('lotus-soup')
        self.page.locator('[data-action="data"]').first.click()
        with self.page.expect_download() as info:
            self.page.locator('[data-action="export"]').click()
        path = RESULTS / 'test-backup.json'
        info.value.save_as(path)
        exported = json.loads(path.read_text())
        self.assertEqual(exported['selected'], ['lotus-soup'])
        exported['servings'] = 4
        self.page.locator('#import-file').set_input_files({'name': 'backup.json', 'mimeType': 'application/json', 'buffer': json.dumps(exported).encode()})
        self.page.locator('#confirm-button').click()
        self.assertEqual(self.saved()['servings'], 4)
        self.page.locator('[data-action="data"]').first.click()
        self.page.locator('#import-file').set_input_files({'name': 'bad.json', 'mimeType': 'application/json', 'buffer': b'{"version":1}'})
        expect(self.page.locator('#import-status')).to_contain_text('格式不正确')
        self.assertEqual(self.saved()['servings'], 4)

    def test_10_hide_purchased_and_new_trip_preserves_recipes(self):
        self.select('pea-shoots')
        self.tab('shopping')
        self.page.locator('.purchase-check').first.click()
        count = self.page.locator('.grocery-row').count()
        self.page.locator('#hide-done').check()
        self.assertEqual(self.page.locator('.grocery-row').count(), count - 1)
        self.page.get_by_label('重置选购清单', exact=True).click()
        self.page.locator('#confirm-button').click()
        self.assertEqual(self.saved()['selected'], [])
        self.assertEqual(len(self.saved()['recipes']), 11)

    def test_11_responsive_views_dialogs_and_touch_targets(self):
        for width in [320, 360, 390, 430, 768, 1024, 1440]:
            with self.subTest(width=width):
                self.page.set_viewport_size({'width': width, 'height': 900 if width >= 768 else 844})
                for tab in ['market', 'recipes', 'shopping', 'pantry']:
                    self.tab(tab)
                    self.assertFalse(self.page.evaluate('document.documentElement.scrollWidth > innerWidth'), f'{width} / {tab} overflow')
                    self.assertEqual(self.page.locator('h1').count(), 1)
                    self.assertTrue(self.page.locator('h1').is_visible())
                self.tab('recipes')
                self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
                self.page.locator('[data-action="edit-recipe"]').click()
                self.assertFalse(self.page.locator('#editor-dialog').evaluate('(el)=>el.scrollWidth>el.clientWidth'))
                self.page.get_by_label('关闭编辑', exact=True).click()
                if width in [390, 1440]:
                    self.page.screenshot(path=str(RESULTS / f'recipes-{width}.png'), full_page=True)
        self.page.set_viewport_size({'width': 390, 'height': 844})
        for selector in ['.recipe-add', '.recipe-title', '.chip', '.recipes-portion .stepper button', '.mobile-nav button']:
            for node in self.page.locator(selector).all():
                self.assertGreaterEqual(node.bounding_box()['height'], 44, selector)

    def test_12_app_has_no_external_asset_requests(self):
        urls = []
        self.page.on('request', lambda request: urls.append(request.url))
        self.page.reload()
        self.assertTrue(urls)
        self.assertTrue(all(url.startswith(self.url.rsplit('/', 1)[0]) for url in urls))
        self.select('tomato-egg')
        self.context.set_offline(True)
        self.tab('shopping')
        self.page.locator('[data-grocery="tomato"] .purchase-check').click()
        self.assertIn('tomato', self.saved()['checked'])

    def test_13_text_is_escaped_in_custom_data(self):
        self.tab('shopping')
        self.page.get_by_role('button', name='加一样', exact=True).click()
        self.page.locator('#item-name').fill('<img src=x onerror=alert(1)>')
        self.page.locator('#item-form button[type="submit"]').click()
        self.assertEqual(self.page.locator('.grocery-row img').count(), 0)
        self.assertIn('<img src=x onerror=alert(1)>', self.page.locator('.grocery-row').inner_text())

    def new_trip(self):
        self.page.locator('[data-action="data"]').first.click()
        self.page.locator('#data-dialog [data-action="new-trip"]').click()
        self.page.locator('#confirm-button').click()

    def buy_one(self, item):
        self.tab('market')
        self.page.locator(f'[data-market-id="{item}"] .market-add').click()
        if self.page.locator('#reminder-dialog').is_visible():
            self.page.locator(f'#reminder-items input[value="{item}"]').check()
            self.page.locator('#reminder-continue').click()
        self.tab('shopping')
        self.page.locator(f'[data-grocery="{item}"] .purchase-check').click()

    def test_14_market_addition_is_unique_and_new_goods_stay_available(self):
        self.tab('market')
        self.page.locator('[data-market-id="tomato"] .market-add').click()
        self.page.locator('[data-market-id="tomato"] .market-add').click()
        self.assertEqual(len(self.saved()['manual']), 1)
        self.assertEqual(self.page.locator('[data-grocery="tomato"]').count(), 1)
        self.page.get_by_role('button', name='加一样', exact=True).click()
        self.page.locator('#item-name').fill('牛奶')
        self.page.locator('#item-category').select_option('protein')
        self.page.locator('#item-form button[type="submit"]').click()
        self.new_trip()
        self.tab('market')
        self.assertIn('牛奶', self.page.locator('#market-content').inner_text())
        self.assertEqual(self.saved()['manual'], [])

    def test_15_consumption_slider_survives_reset_and_restock(self):
        self.buy_one('soy')
        self.assertEqual(self.saved()['levels'][0]['percent'], 100)
        self.assertEqual(len(self.saved()['history']), 1)
        self.tab('pantry')
        self.page.locator('#level-soy').evaluate("el=>{el.value='35';el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}")
        self.new_trip()
        self.assertEqual(self.saved()['levels'][0]['percent'], 35)
        self.assertEqual(len(self.saved()['history']), 1)
        self.tab('recipes')
        self.select('mince-rice')
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="soy"]').count(), 0)
        self.tab('market')
        self.page.locator('[data-market-id="soy"] .market-add').click()
        expect(self.page.locator('#reminder-dialog')).to_be_visible()
        self.assertIn('35%', self.page.locator('#reminder-items').inner_text())
        self.page.locator('#reminder-continue').click()
        self.assertFalse(any(m['id'] == 'soy' for m in self.saved()['manual']))
        self.page.locator('[data-market-id="soy"] .market-add').click()
        self.page.locator('#reminder-items input').check()
        self.page.locator('#reminder-continue').click()
        self.assertEqual(self.saved()['levels'][0]['percent'], 35)
        self.tab('shopping')
        self.page.locator('[data-grocery="soy"] .purchase-check').click()
        self.assertEqual(self.saved()['levels'][0]['percent'], 100)
        self.page.locator('[data-grocery="soy"] .purchase-check').click()
        self.assertEqual(self.saved()['levels'][0]['percent'], 35)
        self.assertEqual(len(self.saved()['history']), 1)

    def test_16_seven_day_fresh_food_warning_on_recipe_selection(self):
        self.buy_one('egg')
        self.new_trip()
        self.tab('recipes')
        self.select('tomato-egg')
        expect(self.page.locator('#reminder-dialog')).to_be_visible()
        self.assertIn('鸡蛋', self.page.locator('#reminder-items').inner_text())
        self.page.locator('#reminder-continue').click()
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="egg"]').count(), 0)
        self.new_trip()
        self.tab('recipes')
        self.select('tomato-egg')
        self.page.locator('#reminder-items input[value="egg"]').check()
        self.page.locator('#reminder-continue').click()
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="egg"]').count(), 1)

    def test_17_unchecking_purchase_retracts_only_current_record(self):
        self.buy_one('egg')
        self.assertEqual(len(self.saved()['history']), 1)
        self.page.locator('[data-grocery="egg"] .purchase-check').click()
        self.assertEqual(self.saved()['history'], [])
        self.assertNotIn('egg', self.saved()['stock'])

    def test_18_daily_reset_is_opt_in_and_preserves_kitchen(self):
        self.buy_one('oil')
        self.page.evaluate("k=>{let s=JSON.parse(localStorage.getItem(k));s.trip.date='2000-01-01';localStorage.setItem(k,JSON.stringify(s));}", KEY)
        self.page.reload()
        self.assertEqual(len(self.saved()['manual']), 1, 'Daily reset must be off by default')
        self.page.locator('[data-action="data"]').first.click()
        self.page.locator('#auto-reset-toggle').check()
        self.page.get_by_label('关闭数据管理', exact=True).click()
        self.page.evaluate("k=>{let s=JSON.parse(localStorage.getItem(k));s.trip.date='2000-01-01';localStorage.setItem(k,JSON.stringify(s));}", KEY)
        self.page.reload()
        self.assertEqual(self.saved()['manual'], [])
        self.assertEqual(self.saved()['checked'], [])
        self.assertEqual(len(self.saved()['history']), 1)
        self.assertEqual(self.saved()['levels'][0]['percent'], 100)

    def test_19_history_shows_30_days_and_retains_older_records(self):
        self.buy_one('egg')
        self.page.evaluate("""k=>{let s=JSON.parse(localStorage.getItem(k));let old={...s.history[0],id:'old-record',boughtAt:new Date(Date.now()-31*86400000).toISOString()};s.history.push(old);localStorage.setItem(k,JSON.stringify(s));}""", KEY)
        self.page.reload()
        self.tab('pantry')
        self.page.locator('[data-action="kitchen-tab"][data-kitchen="history"]').click()
        self.assertEqual(self.page.locator('.history-row').count(), 1)
        self.assertEqual(len(self.saved()['history']), 2)

    def test_20_old_backup_migrates_without_losing_menu(self):
        self.select('tomato-soup')
        self.page.evaluate("""k=>{let s=JSON.parse(localStorage.getItem(k));for(const n of ['history','levels','trip','autoReset','checkLinks','confirmedStock'])delete s[n];s.recipes=s.recipes.filter(r=>r.id!=='cress-soup');s.ingredients=s.ingredients.filter(i=>i.id!=='cooking-wine');localStorage.setItem(k,JSON.stringify(s));}""", KEY)
        self.page.reload()
        self.assertEqual(self.saved()['selected'], ['tomato-soup'])
        self.assertEqual(len(self.saved()['recipes']), 11)
        self.assertTrue(any(i['id'] == 'cooking-wine' for i in self.saved()['ingredients']))
        self.assertEqual(self.saved()['history'], [])

    def test_21_corrupt_saved_data_is_not_overwritten_on_open(self):
        self.page.evaluate('(k)=>localStorage.setItem(k,"broken backup")', KEY)
        self.page.reload()
        self.assertEqual(self.page.evaluate('(k)=>localStorage.getItem(k)', KEY), 'broken backup')
        self.assertTrue(self.page.locator('#storage-warning').is_visible())
        self.tab('market')
        self.assertEqual(self.page.evaluate('(k)=>localStorage.getItem(k)', KEY), 'broken backup')

    def test_22_recent_but_empty_condiment_can_be_skipped_for_this_trip(self):
        self.buy_one('soy')
        self.tab('pantry')
        self.page.locator('#level-soy').evaluate("el=>{el.value='0';el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));}")
        self.new_trip()
        self.tab('recipes')
        self.select('mince-rice')
        expect(self.page.locator('#reminder-dialog')).to_be_visible()
        self.page.locator('#reminder-continue').click()
        self.tab('shopping')
        self.assertEqual(self.page.locator('[data-grocery="soy"]').count(), 0)
        self.assertEqual(self.saved()['levels'][0]['percent'], 0, 'Skipping a purchase must not invent a stock quantity')


    def test_23_add_inventory_without_buying_and_preserve_on_reset(self):
        self.tab('pantry')
        self.page.locator('#inventory-add').click()
        self.page.locator('#item-name').fill('黑醋')
        self.page.locator('#item-name').press('Escape')
        self.page.locator('#item-level').fill('40')
        self.page.locator('#item-submit').click()
        saved = self.saved()
        item = next(i for i in saved['ingredients'] if i['name'] == '黑醋')
        self.assertTrue(item['lasting'])
        self.assertEqual(next(x['percent'] for x in saved['levels'] if x['id'] == item['id']), 40)
        self.assertEqual(saved['manual'], [])
        self.assertEqual(saved['history'], [])
        self.page.locator('[data-kitchen="fresh"]').click()
        self.page.locator('#inventory-add').click()
        self.page.locator('#item-name').fill('生菜')
        self.page.locator('#item-name').press('Escape')
        self.page.locator('#item-have').check()
        self.page.locator('#item-submit').click()
        fresh = next(i for i in self.saved()['ingredients'] if i['name'] == '生菜')
        self.assertIn(fresh['id'], self.saved()['stock'])
        self.page.evaluate('startNewTrip()')
        self.assertIn(fresh['id'], self.saved()['stock'])
        self.assertEqual(self.saved()['history'], [])
        self.assertEqual(next(x['percent'] for x in self.saved()['levels'] if x['id'] == item['id']), 40)

    def test_24_icon_picker_keyboard_alias_and_unknown_level(self):
        self.tab('shopping')
        self.page.get_by_role('button', name='加一样', exact=True).click()
        self.page.locator('#item-name').fill('西红柿')
        expect(self.page.locator('#item-suggestions')).to_be_visible()
        self.assertEqual(self.page.locator('#item-suggestions [role=option]').count(), 1)
        self.assertEqual(self.page.locator('#item-suggestions svg').count(), 1)
        self.page.locator('#item-name').press('ArrowDown')
        self.page.locator('#item-name').press('Enter')
        expect(self.page.locator('#item-name')).to_have_value('番茄')
        expect(self.page.locator('#item-suggestions')).to_be_hidden()
        self.page.locator('#item-submit').click()
        self.assertEqual(self.saved()['manual'][0]['id'], 'tomato')
        self.tab('pantry')
        self.page.locator('#inventory-add').click()
        self.page.locator('#item-name').fill('老抽')
        self.page.locator('#item-name').press('Escape')
        self.page.locator('#item-submit').click()
        item = next(i for i in self.saved()['ingredients'] if i['name'] == '老抽')
        self.assertFalse(any(x['id'] == item['id'] for x in self.saved()['levels']))
        self.assertIn('未记录', self.page.locator(f'[data-pantry-id="{item["id"]}"]').inner_text())

    def test_25_popups_centered_at_phone_and_desktop_widths(self):
        for width in [320, 390, 768, 1440]:
            self.page.set_viewport_size({'width': width, 'height': 844})
            self.page.evaluate('showAddItem()')
            self.page.locator('#item-name').press('Escape')
            box = self.page.locator('#item-dialog').bounding_box()
            self.assertLessEqual(abs(box['x'] + box['width'] / 2 - width / 2), 1)
            self.assertLessEqual(abs(box['y'] + box['height'] / 2 - 844 / 2), 2)
            self.assertGreaterEqual(box['x'], 0)
            self.assertLessEqual(box['x'] + box['width'], width)
            self.assertFalse(self.page.evaluate('document.documentElement.scrollWidth>innerWidth'))
            if width == 390:
                self.page.screenshot(path=str(RESULTS / 'phone-add-item.png'))
            self.page.locator('#item-dialog [data-action="close"]').click()


    def test_26_source_links_auto_append_filter_blanks_and_persist(self):
        self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
        self.page.locator('[data-action="edit-recipe"]').click()
        self.assertEqual(self.page.locator('.source-input').count(), 1)
        self.page.locator('#edit-source').fill('https://www.xiaohongshu.com/explore/first')
        self.assertEqual(self.page.locator('.source-input').count(), 2)
        self.assertEqual(self.page.locator('.source-input').nth(1).input_value(), '')
        self.page.locator('.source-input').nth(1).fill('https://example.com/recipe')
        self.assertEqual(self.page.locator('.source-input').count(), 3)
        self.page.locator('.source-input').nth(0).clear()
        self.page.locator('.source-input').nth(2).fill('https://www.xiaohongshu.com/explore/second')
        self.assertEqual(self.page.locator('.source-input').count(), 4)
        self.page.locator('#recipe-form button[type="submit"]').click()
        sources = ['https://example.com/recipe', 'https://www.xiaohongshu.com/explore/second']
        self.assertEqual(self.saved()['recipes'][0]['sources'], sources)
        self.assertEqual(self.saved()['recipes'][0]['source'], sources[0])
        self.page.reload()
        self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
        links = self.page.locator('#detail-body .detail-source')
        self.assertEqual(links.count(), 2)
        self.assertEqual([link.get_attribute('href') for link in links.all()], sources)
        self.page.locator('[data-action="edit-recipe"]').click()
        self.assertEqual(self.page.locator('.source-input').count(), 3)
        self.assertEqual([node.input_value() for node in self.page.locator('.source-input').all()], sources + [''])
        self.page.locator('.source-input').nth(0).clear()
        self.page.locator('.source-input').nth(1).clear()
        self.page.locator('#recipe-form button[type="submit"]').click()
        self.assertEqual(self.saved()['recipes'][0]['sources'], [])
        self.assertEqual(self.saved()['recipes'][0]['source'], '')
        self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
        self.assertEqual(self.page.locator('#detail-body .detail-source').count(), 0)

    def test_27_legacy_source_migrates_and_unsafe_sources_rejected(self):
        saved = self.saved()
        saved['recipes'][0]['source'] = 'https://example.com/old-note'
        saved['recipes'][0].pop('sources', None)
        self.page.evaluate('([key,value])=>localStorage.setItem(key,JSON.stringify(value))', [KEY, saved])
        self.page.reload()
        self.page.locator('[data-recipe="tomato-egg"] .art-open').click()
        expect(self.page.locator('#detail-body .detail-source')).to_have_attribute('href', 'https://example.com/old-note')
        self.page.locator('[data-action="edit-recipe"]').click()
        self.assertEqual([node.input_value() for node in self.page.locator('.source-input').all()], ['https://example.com/old-note', ''])
        self.page.locator('#edit-source').fill('javascript:alert(1)')
        self.page.locator('#recipe-form button[type="submit"]').click()
        expect(self.page.locator('#recipe-error')).to_be_visible()
        self.assertEqual(self.saved()['recipes'][0]['source'], 'https://example.com/old-note')
        saved['recipes'][0]['sources'] = ['javascript:alert(1)']
        self.assertTrue(self.page.evaluate('(value)=>{try{validateState(value);return false;}catch{return true;}}', saved))


if __name__ == '__main__':
    unittest.main(verbosity=2)
