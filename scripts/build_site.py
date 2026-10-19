"""Build only the public app, never publish repository tooling or account credentials."""
from pathlib import Path
import base64
import json
import os
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = '{"supabaseUrl":"","publishableKey":""}'


def validate_config(url, key):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.hostname
            or not re.fullmatch(r'[a-z0-9-]+\.supabase\.co', parsed.hostname)
            or parsed.username or parsed.password or parsed.port
            or parsed.query or parsed.fragment or parsed.path not in ['', '/']):
        raise ValueError('SUPABASE_URL must be the HTTPS project URL, e.g. https://project.supabase.co')
    if key.startswith('sb_secret_'):
        raise ValueError('Never publish a secret/service-role key. Use a publishable or anon key.')
    if key.startswith('sb_publishable_') and re.fullmatch(r'sb_publishable_[A-Za-z0-9_-]{10,}', key):
        return {'supabaseUrl': url.rstrip('/'), 'publishableKey': key}
    try:
        part = key.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
        if len(key.split('.')) != 3 or claims.get('role') != 'anon':
            raise ValueError()
    except (ValueError, KeyError, IndexError, TypeError):
        raise ValueError('Expected a Supabase publishable key or legacy anon JWT, never an admin key.') from None
    return {'supabaseUrl': url.rstrip('/'), 'publishableKey': key}


def build(output, url='', key='', require_cloud=False):
    source = (ROOT / 'little-basket.html').read_text()
    if source.count(PLACEHOLDER) != 1:
        raise ValueError('Expected exactly one cloud configuration placeholder')
    if bool(url) != bool(key) or (require_cloud and not url):
        raise ValueError('Set both public configuration values in site-config.json or SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.')
    config = validate_config(url, key) if url else {'supabaseUrl': '', 'publishableKey': ''}
    encoded = json.dumps(config, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    html = source.replace(PLACEHOLDER, encoded)
    output = Path(output)
    # Caller chooses an output folder. Never clean the checkout or an existing folder blindly.
    output.mkdir(parents=True, exist_ok=True)
    for name in ['index.html', 'little-basket.html']:
        (output / name).write_text(html)
    (output / '.nojekyll').write_text('')
    print('Built standalone HTML. Cloud configuration: ' + ('enabled' if url else 'not configured'))


if __name__ == '__main__':
    try:
        public_config = json.loads((ROOT / 'site-config.json').read_text()) if (ROOT / 'site-config.json').exists() else {}
        build(ROOT / 'dist', os.environ.get('SUPABASE_URL') or public_config.get('supabaseUrl', ''),
              os.environ.get('SUPABASE_PUBLISHABLE_KEY') or public_config.get('publishableKey', ''), '--require-cloud' in sys.argv)
    except ValueError as error:
        raise SystemExit(str(error)) from None
