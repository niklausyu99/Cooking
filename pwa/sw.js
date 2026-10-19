/* Only public app files are cached. Supabase and family data are never intercepted. */
const BASE = new URL('./', self.registration.scope);
const PREFIX = 'little-basket-shell-' + encodeURIComponent(BASE.pathname) + '-';
const CACHE = PREFIX + '__APP_VERSION__';
const SHELL = BASE.href;
const FILES = ['', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/apple-touch-icon.png', 'icons/favicon.png'].map(path => new URL(path, BASE).href);
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(FILES.map(url => new Request(url, {cache: 'reload'})))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith(PREFIX) && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== BASE.origin) return;
  const appPaths = ['', 'index.html', 'little-basket.html'].map(path => new URL(path, BASE).pathname);
  if (request.mode === 'navigate' && appPaths.includes(url.pathname)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const response = await fetch(new Request(request, {cache: 'no-store'}));
        if (response.ok && (response.headers.get('content-type') || '').includes('text/html')) await cache.put(SHELL, response.clone());
        return response;
      } catch {
        return (await cache.match(SHELL)) || new Response('首次打开菜篮子需要联网，之后可离线使用。', {status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8'}});
      }
    })());
  } else if (FILES.includes(url.href)) {
    event.respondWith(caches.open(CACHE).then(async cache => (await cache.match(request)) || fetch(request)));
  }
});
