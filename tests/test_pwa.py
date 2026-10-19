"""Exercise the built installable app on a real service worker, including offline reload."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import threading
import unittest

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_site.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class PWATests(unittest.TestCase):
    def test_installable_scope_offline_reload_and_private_data_not_cached(self):
        with tempfile.TemporaryDirectory() as directory, sync_playwright() as pw:
            output = Path(directory) / 'Little-Basket'
            builder.build(output)
            server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=directory))
            threading.Thread(target=server.serve_forever, daemon=True).start()
            browser = pw.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
            try:
                url = f'http://127.0.0.1:{server.server_port}/Little-Basket/'
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(url)
                page.wait_for_function('navigator.serviceWorker.controller!==null')
                scope = page.evaluate('navigator.serviceWorker.ready.then(r=>r.scope)')
                self.assertEqual(scope, url)
                session = context.new_cdp_session(page)
                manifest = session.send('Page.getAppManifest')
                self.assertEqual(manifest['errors'], [])
                self.assertEqual(json.loads(manifest['data'])['display'], 'standalone')
                page.locator('[data-market-id=blueberry] .market-add').click()
                page.locator('.mobile-nav [data-view=pantry]').click()
                page.locator('[data-kitchen=fresh]').click()
                page.locator('[data-pantry-id=egg] [data-amount="2"]').click()
                context.set_offline(True)
                page.reload()
                expect(page.locator('[data-kitchen=fresh]')).to_have_attribute('aria-pressed', 'true')
                expect(page.locator('#fresh-egg')).to_have_value('2')
                self.assertTrue(page.evaluate("state.manual.some(x=>x.id==='blueberry')"))
                urls = page.evaluate('caches.keys().then(keys=>Promise.all(keys.map(k=>caches.open(k).then(c=>c.keys()).then(req=>req.map(r=>r.url))))).then(x=>x.flat())')
                self.assertTrue(urls)
                self.assertTrue(all(cached.startswith(scope) for cached in urls))
                self.assertFalse(any('family=' in cached or 'supabase' in cached for cached in urls))
                self.assertEqual(errors, [])
            finally:
                context.close()
                browser.close()
                server.shutdown()
                server.server_close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
