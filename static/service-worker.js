const CACHE_NAME = 'gentech-static-v1';
const RUNTIME = 'gentech-runtime';
const PRECACHE_URLS = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Navigation requests (app shell)
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then(resp => resp).catch(() => caches.match('/'))
    );
    return;
  }

  // Cache-first for audio files
  if (url.pathname.startsWith('/static/audio') || url.pathname.endsWith('.mp3') || url.pathname.endsWith('.wav')) {
    event.respondWith(
      caches.open(RUNTIME).then(cache =>
        cache.match(req).then(response =>
          response || fetch(req).then(networkResponse => {
            cache.put(req, networkResponse.clone()).catch(()=>{});
            return networkResponse;
          }).catch(()=>response)
        )
      )
    );
    return;
  }

  // Cache-first for JSON (lessons)
  if (url.pathname.endsWith('.json') || url.pathname.includes('/languages/')) {
    event.respondWith(
      caches.open(RUNTIME).then(cache =>
        cache.match(req).then(response =>
          response || fetch(req).then(networkResponse => {
            cache.put(req, networkResponse.clone()).catch(()=>{});
            return networkResponse;
          }).catch(()=>response)
        )
      )
    );
    return;
  }

  // Default: try cache, then network
  event.respondWith(
    caches.match(req).then(response => response || fetch(req))
  );
});
