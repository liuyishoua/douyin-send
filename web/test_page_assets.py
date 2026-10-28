from pathlib import Path
import re
import tempfile
import unittest
try:
    from flask import Flask
except ImportError:
    Flask = None
from web.page_assets import PageAssets, install_pages


class PageAssetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'app.js').write_text("import './dependency.js'; document.title='ready';")
        (self.root / 'dependency.js').write_text("export const value='v1';")
        (self.root / 'style.css').write_text('body{color:red;background:url(./icon.svg)}')
        (self.root / 'icon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        (self.root / 'index.html').write_text('<link rel="stylesheet" href="/static/style.css"><div id="app"></div><script type="module" src="/static/app.js"></script>')
    def tearDown(self):
        self.tmp.cleanup()

    def test_entries_link_versioned_assets_and_preserve_module_semantics(self):
        renderer = PageAssets(self.root)
        html, hashes = renderer.render('index.html')
        self.assertIn('src="/static/app.js?asset_version=', html)
        self.assertIn('href="/static/style.css?asset_version=', html)
        self.assertIn('type="module"', html)
        self.assertNotIn("document.title='ready'", html)
        self.assertFalse(hashes)
        self.assertIn('/static/dependency.js?asset_version=' + renderer.version, renderer.content('app.js').decode())
        self.assertIn('/static/icon.svg?asset_version=' + renderer.version, renderer.content('style.css').decode())

    def test_dependency_change_versions_parent_and_cached_content(self):
        renderer = PageAssets(self.root)
        before, _ = renderer.render('index.html')
        old_script = renderer.content('app.js')
        (self.root / 'dependency.js').write_text("export const value='changed';")
        after, _ = renderer.render('index.html')
        self.assertNotEqual(before, after)
        self.assertNotEqual(old_script, renderer.content('app.js'))

    def test_small_theme_bootstrap_has_an_exact_hash_and_module_preload(self):
        import base64, hashlib
        code="document.documentElement.dataset.theme='dark';"
        (self.root / 'theme.js').write_text(code)
        (self.root / 'index.html').write_text('<head><script src="/static/theme.js"></script></head><script type="module" src="/static/app.js"></script>')
        html, hashes = PageAssets(self.root).render('index.html')
        self.assertIn('<script>' + code + '</script>', html)
        digest="'sha256-" + base64.b64encode(hashlib.sha256(code.encode()).digest()).decode() + "'"
        self.assertIn(digest, hashes['script-src'])
        self.assertIn('rel="modulepreload"', html)
        self.assertIn('src="/static/app.js?asset_version=', html)

    def test_import_cycles_share_a_version_without_recursion(self):
        (self.root / 'dependency.js').write_text("import './app.js';")
        renderer = PageAssets(self.root)
        self.assertIn('asset_version=' + renderer.version, renderer.content('dependency.js').decode())

    def test_external_and_traversing_assets_remain_outside_public_manifest(self):
        renderer = PageAssets(self.root)
        for url in ('https://example.invalid/app.js', '//example.invalid/app.js', '/static/../../private.js'):
            self.assertIsNone(renderer.asset(url))
            self.assertEqual(renderer.asset_url(url), url)

    def test_local_bundle_substitution(self):
        (self.root / 'app.bundle.mjs').write_text('bundled()')
        renderer = PageAssets(self.root, {'app.js': 'app.bundle.mjs'})
        html, _ = renderer.render('index.html')
        self.assertIn('src="/static/app.bundle.mjs?asset_version=', html)
        self.assertNotIn('src="/static/app.js?', html)

    @unittest.skipIf(Flask is None, "Flask adapter is verified in Flask workspaces")
    def test_public_assets_cache_but_identity_and_html_do_not(self):
        app = Flask(__name__, static_folder=str(self.root), static_url_path='/static')
        renderer = install_pages(app, {'index.html'})
        @app.after_request
        def security(response):
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'"
            return response
        @app.get('/')
        def index():
            return app.send_static_file('index.html')
        @app.get('/api/me')
        def identity():
            return {'id': 1}
        client = app.test_client()
        html = client.get('/')
        self.assertIn('no-store', html.headers['Cache-Control'])
        url = re.search(r'src="([^"]+)"', html.text)[1]
        first = client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertIn('immutable', first.headers['Cache-Control'])
        second = client.get(url, headers={'If-None-Match': first.headers['ETag']})
        self.assertEqual(second.status_code, 304)
        self.assertNotIn('unsafe-inline', first.headers['Content-Security-Policy'])
        self.assertEqual(client.get('/api/me').headers['Cache-Control'], 'no-store')
        self.assertEqual(client.get('/static/app.js').headers['Cache-Control'], 'public, no-cache')
        self.assertNotIn('immutable', client.get('/static/app.js?asset_version=old').headers['Cache-Control'])
