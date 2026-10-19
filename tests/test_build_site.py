"""Publication checks: public configuration only; repository tooling stays private."""
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_site', ROOT / 'scripts/build_site.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def test_reject_admin_keys_and_nonproject_urls(self):
        claims = base64.urlsafe_b64encode(json.dumps({'role': 'service_role'}).encode()).decode().rstrip('=')
        for key in ['sb_secret_do_not_publish', 'eyJ.' + claims + '.signature']:
            with self.assertRaises(ValueError):
                builder.validate_config('https://test.supabase.co', key)
        for url in ['http://test.supabase.co', 'https://test.supabase.co.evil.test', 'https://test.supabase.co/?token=x']:
            with self.assertRaises(ValueError):
                builder.validate_config(url, 'sb_publishable_fixture_only')

    def test_production_requires_complete_configuration(self):
        with tempfile.TemporaryDirectory() as output:
            for url, key in [('', ''), ('https://test.supabase.co', '')]:
                with self.assertRaises(ValueError):
                    builder.build(output, url, key, require_cloud=True)

    def test_publishes_only_standalone_app_and_public_config(self):
        with tempfile.TemporaryDirectory() as output:
            builder.build(output, 'https://test.supabase.co', 'sb_publishable_fixture_only', require_cloud=True)
            self.assertEqual({p.name for p in Path(output).iterdir()}, {'index.html', 'little-basket.html', '.nojekyll', 'manifest.webmanifest', 'sw.js', 'icons'})
            html = (Path(output) / 'index.html').read_text()
            self.assertIn('https://test.supabase.co', html)
            self.assertNotIn('sb_secret_', html)
            self.assertEqual(html, (Path(output) / 'little-basket.html').read_text())
            self.assertNotIn('cloud-password', html)
            manifest=json.loads((Path(output)/'manifest.webmanifest').read_text())
            self.assertEqual(manifest['display'],'standalone')
            self.assertEqual(manifest['start_url'],'./')
            self.assertEqual(manifest['scope'],'./')
            self.assertNotIn('family=',json.dumps(manifest))
            self.assertNotIn('__APP_VERSION__',(Path(output)/'sw.js').read_text())
            self.assertIn('apple-mobile-web-app-capable',html)
            self.assertNotIn('source.png',{p.name for p in Path(output).rglob('*')})


if __name__ == '__main__':
    unittest.main(verbosity=2)
