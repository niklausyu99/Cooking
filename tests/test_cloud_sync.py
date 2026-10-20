"""Browser integration tests using a revisioned RPC stub, not a real Supabase project."""
from pathlib import Path
import copy
import json
import os
import shutil
import unittest
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://basket.example.test/'
BACKEND = 'https://basket-test.supabase.co'
KEY_A = 'a' * 64
KEY_B = 'b' * 64
FAMILY_A = '11111111-1111-4111-8111-111111111111'
FAMILY_B = '22222222-2222-4222-8222-222222222222'
CONFIG = json.dumps({'supabaseUrl': BACKEND, 'publishableKey': 'sb_publishable_test_fixture_only'}, separators=(',', ':'))
HTML = (ROOT / 'little-basket.html').read_text().replace('{"supabaseUrl":"","publishableKey":""}', CONFIG)


class FamilySyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=os.environ.get('BASKET_CHROMIUM') or shutil.which('chromium'), args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.contexts = []
        self.errors = []
        self.requests = []
        self.offline = False
        self.race = False
        self.db = {KEY_A: {'family_id': FAMILY_A, 'revision': 0, 'state': None}, KEY_B: {'family_id': FAMILY_B, 'revision': 0, 'state': None}}

    def tearDown(self):
        for context in self.contexts:
            context.close()
        self.assertEqual(self.errors, [])

    def rpc(self, route):
        if self.offline:
            route.abort('internetdisconnected')
            return
        request = route.request
        if request.method == 'OPTIONS':
            route.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': 'POST, OPTIONS'})
            return
        body = request.post_data_json
        self.requests.append((request.url.rsplit('/', 1)[-1], copy.deepcopy(body)))
        row = self.db.get(body.get('access_key'))
        status = 200
        if not row:
            status, result = 403, {'code': 'PT403'}
        elif request.url.endswith('/read_family_kitchen'):
            result = {k: v for k, v in row.items() if k != 'state'}
            result.update(updated_at='2026-10-19T00:00:00Z', has_state=row['state'] is not None)
            if body['known_revision'] != row['revision']:
                result['state'] = copy.deepcopy(row['state'])
        elif request.url.endswith('/sync_family_kitchen'):
            if self.race:
                row['revision'] += 1
                row['state']['manual'] = [{'id': 'potato', 'note': '家人刚加的'}]
                self.race = False
            if body['expected_revision'] != row['revision']:
                status, result = 409, {'code': 'PT409'}
            else:
                row['state'] = copy.deepcopy(body['new_state'])
                row['revision'] += 1
                result = {k: v for k, v in row.items() if k != 'state'}
                result['updated_at'] = '2026-10-19T00:00:00Z'
        else:
            self.fail('Unexpected cloud endpoint')
        route.fulfill(status=status, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(result))

    def device(self, key=KEY_A, guest=None):
        context = self.browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce', accept_downloads=True)
        self.contexts.append(context)
        context.route(URL + '**', lambda route: route.fulfill(content_type='text/html', body=HTML))
        context.route(BACKEND + '/**', self.rpc)
        if guest:
            context.add_init_script('localStorage.setItem("little-basket:v1", ' + json.dumps(json.dumps(guest)) + ');')
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.goto(URL + ('#family=' + key if key is not None else ''))
        return page

    def ready(self, page):
        expect(page.locator('#cloud-button-label')).to_have_text('已同步', timeout=10000)

    def sync(self, page):
        page.evaluate('cloudEngine.sync()')

    def add(self, page, ingredient='tomato'):
        page.evaluate('(id)=>mutate(()=>addManual(id,"测试"))', ingredient)

    def test_direct_link_no_login_remembers_and_shares_no_credential_in_state(self):
        page = self.device()
        self.ready(page)
        self.assertEqual(page.locator('input[type=password], input[type=email]').count(), 0)
        self.assertEqual(page.evaluate('location.hash'), '')
        self.assertEqual(page.evaluate('cloudEngine.connection.familyId'), FAMILY_A)
        self.assertNotIn(KEY_A, page.evaluate('JSON.stringify(state)'))
        self.assertEqual({name for name, _ in self.requests}, {'read_family_kitchen', 'sync_family_kitchen'})
        page.reload()
        self.ready(page)
        self.assertEqual(page.evaluate('cloudEngine.connection.familyId'), FAMILY_A)

    def test_two_devices_cart_inventory_and_purchase_history(self):
        first = self.device()
        self.ready(first)
        second = self.device()
        self.ready(second)
        self.add(first)
        self.sync(first)
        self.sync(second)
        self.assertEqual(second.evaluate('state.manual[0].id'), 'tomato')
        second.evaluate("mutate(()=>setLevel('soy',35))")
        second.evaluate("togglePurchase('tomato')")
        self.sync(second)
        self.sync(first)
        self.assertEqual(first.evaluate("state.levels.find(x=>x.id==='soy').percent"), 35)
        self.assertEqual(first.evaluate('state.history.length'), 1)
        self.assertIn('tomato', first.evaluate('state.checked'))
        self.assertIn('tomato', first.evaluate('state.stock'))

    def test_offline_queue_survives_reload_and_reconnect(self):
        page = self.device()
        self.ready(page)
        self.offline = True
        self.add(page)
        self.sync(page)
        expect(page.locator('#cloud-button-label')).to_have_text('离线暂存')
        page.reload()
        expect(page.locator('#cloud-button-label')).to_have_text('离线暂存')
        self.assertEqual(page.evaluate('state.manual[0].id'), 'tomato')
        self.offline = False
        self.sync(page)
        self.ready(page)
        self.assertEqual(self.db[KEY_A]['state']['manual'][0]['id'], 'tomato')

    def test_new_recipe_manual_stock_and_history_deletion_sync(self):
        first = self.device()
        self.ready(first)
        second = self.device()
        self.ready(second)
        first.locator('.mobile-nav [data-view=recipes]').click()
        first.locator('#add-recipe-button').click()
        first.locator('#edit-title').fill('家人的燕麦早餐')
        first.locator('.ing-name').first.fill('燕麦')
        first.locator('#recipe-form button[type=submit]').click()
        first.evaluate("setInventoryStock('egg',true,2);addManual('banana');persist();togglePurchase('banana')")
        self.sync(first)
        self.sync(second)
        self.assertTrue(second.evaluate("state.recipes.some(r=>r.title==='家人的燕麦早餐'&&r.learning)"))
        self.assertTrue(second.evaluate("state.stockEdits.some(x=>x.id==='egg'&&x.freshAmount===2)"))
        self.assertEqual(second.evaluate("freshStock('egg').amount"),2)
        self.assertEqual(second.evaluate('state.history.length'), 1)
        second.evaluate('removePurchaseRecord(state.history[0].id)')
        second.locator('#confirm-button').click()
        self.sync(second)
        self.sync(first)
        self.assertEqual(first.evaluate('state.history.length'), 0)
        self.assertNotIn('banana', first.evaluate('state.checked'))
        self.assertNotIn('data:image', json.dumps(self.db[KEY_A]['state']))

    def test_concurrent_edits_require_choice_then_backup_and_resolve(self):
        first = self.device()
        self.ready(first)
        second = self.device()
        self.ready(second)
        self.add(first, 'tomato')
        self.add(second, 'potato')
        self.sync(first)
        self.sync(second)
        expect(second.locator('#cloud-conflict')).to_be_visible()
        self.assertEqual(second.evaluate('state.manual[0].id'), 'potato')
        self.assertEqual(self.db[KEY_A]['state']['manual'][0]['id'], 'tomato')
        with second.expect_download() as download:
            second.locator('#cloud-use-remote').click()
        self.assertTrue(download.value.suggested_filename.endswith('.json'))
        self.ready(second)
        self.assertEqual(second.evaluate('state.manual[0].id'), 'tomato')

    def test_compare_and_swap_race_does_not_overwrite_family(self):
        page = self.device()
        self.ready(page)
        self.add(page)
        self.race = True
        self.sync(page)
        expect(page.locator('#cloud-conflict')).to_be_visible()
        self.assertEqual(self.db[KEY_A]['state']['manual'][0]['id'], 'potato')
        self.assertEqual(page.evaluate('state.manual[0].id'), 'tomato')

    def test_guest_migration_explicit_and_keeps_original_local_copy(self):
        seed = self.device(None)
        self.add(seed)
        guest = seed.evaluate('state')
        page = self.device(guest=guest)
        expect(page.locator('#cloud-conflict')).to_be_visible()
        self.assertIsNone(self.db[KEY_A]['state'])
        page.locator('#cloud-keep-local').click()
        self.ready(page)
        self.assertEqual(self.db[KEY_A]['state']['manual'][0]['id'], 'tomato')
        self.assertEqual(page.evaluate('JSON.parse(localStorage.getItem("little-basket:v1")).manual[0].id'), 'tomato')

    def test_family_isolation_invalid_link_and_disconnect(self):
        page = self.device()
        self.ready(page)
        self.add(page)
        self.sync(page)
        page.goto(URL + '#family=' + KEY_B)
        page.wait_for_function('(id)=>cloudEngine?.connection?.familyId===id', arg=FAMILY_B)
        self.ready(page)
        self.assertEqual(page.evaluate('cloudEngine.connection.familyId'), FAMILY_B)
        self.assertEqual(page.evaluate('state.manual'), [])
        self.assertEqual(self.db[KEY_A]['state']['manual'][0]['id'], 'tomato')
        page.goto(URL + '#family=' + 'c' * 64)
        expect(page.locator('#cloud-button-label')).to_have_text('链接已失效')
        self.assertEqual(page.evaluate('state.manual'), [])
        self.assertEqual(page.evaluate('JSON.parse(localStorage.getItem(FAMILY_CONNECTION_KEY)).familyId'), FAMILY_B)
        page.evaluate('cloudEngine.disconnect()')
        self.assertIsNone(page.evaluate('cloudEngine.connection'))
        self.assertEqual(page.evaluate('state.manual'), [])

    def test_steady_poll_requests_revision_only_and_navigation_does_not_write(self):
        page = self.device()
        self.ready(page)
        revision = self.db[KEY_A]['revision']
        self.requests.clear()
        page.locator('.mobile-nav [data-view="recipes"]').click()
        self.sync(page)
        self.assertEqual(self.db[KEY_A]['revision'], revision)
        self.assertEqual(self.requests, [('read_family_kitchen', {'access_key': KEY_A, 'known_revision': revision})])

    def test_link_revocation_stops_writes_without_deleting_local_queue(self):
        page = self.device()
        self.ready(page)
        del self.db[KEY_A]
        self.add(page)
        self.sync(page)
        expect(page.locator('#cloud-button-label')).to_have_text('链接已失效')
        self.assertEqual(page.evaluate('state.manual[0].id'), 'tomato')
        page.reload()
        expect(page.locator('#cloud-button-label')).to_have_text('链接已失效')
        self.assertEqual(page.evaluate('state.manual[0].id'), 'tomato')


    def test_multiple_recipe_sources_sync_to_family(self):
        first = self.device()
        self.ready(first)
        second = self.device()
        self.ready(second)
        links = ['https://example.com/first', 'https://example.com/second']
        first.evaluate('(links)=>mutate(()=>{state.recipes[0].sources=links;state.recipes[0].source=links[0];state.recipes[0].origin="我的厨房笔记";})', links)
        self.sync(first)
        self.sync(second)
        self.assertEqual(second.evaluate('state.recipes[0].sources'), links)



    def test_connect_form_accepts_private_code_and_shared_link_without_login(self):
        for raw in [KEY_A, URL+'#family='+KEY_A]:
            page=self.device(None)
            page.locator('#cloud-button').click()
            page.locator('#family-connect-input').fill(raw)
            page.locator('#family-connect-form button[type=submit]').click()
            self.ready(page)
            self.assertEqual(page.evaluate('cloudEngine.connection.familyId'),FAMILY_A)
            self.assertEqual(page.evaluate('location.hash'),'')
            self.assertEqual(page.locator('input[type=password],input[type=email]').count(),0)


    def test_recipe_preview_omissions_sync_without_inventory_changes(self):
        first=self.device()
        self.ready(first)
        second=self.device()
        self.ready(second)
        first.evaluate("requestRecipe('tomato-egg')")
        self.sync(first)
        self.sync(second)
        second.locator('.mobile-nav [data-view=market]').click()
        second.locator('#basket-peek').click()
        second.locator('[data-preview-id=tomato] button').click()
        self.sync(second)
        self.sync(first)
        self.assertNotIn('tomato',first.evaluate('groceryData().list.map(e=>e.id)'))
        self.assertEqual(first.evaluate('state.stock'),[])
        self.assertEqual(first.evaluate('state.history'),[])
        first.evaluate("mutate(()=>addManual('tomato'))")
        self.sync(first)
        self.sync(second)
        expect(second.locator('[data-preview-id=tomato]')).to_be_visible()



    def test_item_and_total_notes_sync_and_preserve_unsent_guest_note(self):
        first=self.device()
        self.ready(first)
        second=self.device()
        self.ready(second)
        self.add(first)
        first.locator('.mobile-nav [data-view=market]').click()
        first.locator('#basket-peek').click()
        first.locator('[data-preview-id=tomato] summary').click()
        first.locator('#basket-preview [data-item-note=tomato]').fill('挑熟一点')
        self.sync(first)
        self.sync(second)
        self.assertEqual(second.evaluate("itemNote('tomato')"),'挑熟一点')
        first.locator('[data-action=basket-full]').click()
        first.locator('.trip-note summary').click()
        first.locator('[data-trip-note]').fill('今天带购物袋')
        self.sync(first)
        self.sync(second)
        self.assertEqual(second.evaluate('state.trip.note'),'今天带购物袋')
        guest=self.device(None)
        guest.locator('.mobile-nav [data-view=shopping]').click()
        guest.locator('.trip-note summary').click()
        guest.locator('[data-trip-note]').fill('还没连接也写了备注')
        self.assertTrue(guest.evaluate('meaningful(state)'))



    def test_family_link_copy_is_visible_reports_success_and_does_not_sync(self):
        page = self.device()
        self.ready(page)
        expect(page.locator('#cloud-button-context')).to_have_text('家庭厨房')
        before = copy.deepcopy(self.db[KEY_A])
        page.locator('#cloud-button').click()
        expect(page.get_by_role('heading', name='家庭专属链接', exact=True)).to_be_visible()
        expect(page.locator('#cloud-copy')).to_be_in_viewport()
        page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copiedFamilyLink=value}})")
        page.locator('#cloud-copy').click()
        expect(page.locator('#cloud-link-feedback')).to_have_text('已复制，可以粘贴发给家人。')
        self.assertEqual(page.evaluate('window.copiedFamilyLink'), URL + '#family=' + KEY_A)
        expect(page.locator('#cloud-share-result')).to_be_hidden()
        self.assertNotIn(KEY_A, page.evaluate('JSON.stringify(state)'))
        self.assertEqual(page.evaluate('location.hash'), '')
        self.assertEqual(self.db[KEY_A], before)

    def test_family_link_manual_copy_and_cancelled_native_share(self):
        page = self.device()
        self.ready(page)
        page.locator('#cloud-button').click()
        page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new DOMException('denied','NotAllowedError')}}})")
        page.locator('#cloud-copy').click()
        expect(page.locator('#cloud-share-link')).to_have_value(URL + '#family=' + KEY_A)
        expect(page.locator('#cloud-share-link')).to_have_attribute('readonly', '')
        expect(page.locator('#cloud-share-link')).to_be_focused()
        expect(page.locator('#cloud-link-feedback')).to_contain_text('请长按下方链接复制')
        page.evaluate("Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('cancelled','AbortError')}})")
        page.locator('#cloud-share').click()
        expect(page.locator('#cloud-link-feedback')).to_have_text('已取消分享，家庭连接不受影响。')
        expect(page.locator('#cloud-dialog')).to_be_visible()
        self.ready(page)
        page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>window.copiedFamilyLink=value}})")
        page.locator('#cloud-copy').click()
        expect(page.locator('#cloud-share-result')).to_be_hidden()
        expect(page.locator('#cloud-share-link')).to_have_value('')

    def test_revoked_family_link_clears_manual_fallback_and_disables_copy(self):
        page = self.device()
        self.ready(page)
        page.locator('#cloud-button').click()
        page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:undefined})")
        page.locator('#cloud-copy').click()
        expect(page.locator('#cloud-share-result')).to_be_visible()
        del self.db[KEY_A]
        self.sync(page)
        expect(page.locator('#cloud-copy')).to_be_disabled()
        expect(page.locator('#cloud-share')).to_be_disabled()
        expect(page.locator('#cloud-share-result')).to_be_hidden()
        expect(page.locator('#cloud-share-link')).to_have_value('')
        expect(page.locator('#cloud-link-feedback')).to_be_hidden()


if __name__ == '__main__':
    unittest.main(verbosity=2)
