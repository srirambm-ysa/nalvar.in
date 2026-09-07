// Nalvar PWA — offline shell cache
const CACHE = 'nalvar-v23';
const SHELL = [
  '/',
  '/manifest.webmanifest',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/maskable-512.png',
  '/icons/apple-touch-icon.png',
  '/icons/favicon.ico',
  // optimized images — precache small set for offline
  '/images/optimized/appar-800.webp',
  '/images/optimized/sambandar-800.webp',
  '/images/optimized/sundarar-800.webp',
  '/images/optimized/manickavasagar-800.webp',
  '/images/siva_with_nandi_transparent.webp',
  '/images/siva_with_nandi_transparent-350w.webp',
  '/images/siva_with_nandi_transparent-525w.webp',
  '/data.json',
  '/remedies.json',
  '/images/nalvar-badge-280.webp',
  '/images/nalvar-badge-360.webp',
  '/images/nalvar-badge-480.webp',
  '/images/nalvar-transparent.webp'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  // only handle GET same-origin
  if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;
  // normalize /index.html → / for cache lookup (Cloudflare serves /index.html as 307 → /)
  const url = new URL(req.url);
  const isIndexHtml = url.pathname === '/index.html';
  const cacheKey = isIndexHtml ? new Request(url.origin + '/', {headers: req.headers}) : req;
  e.respondWith(
    caches.match(cacheKey).then(hit => {
      if (hit) return hit;
      // for /index.html, also try "/" directly
      if (isIndexHtml) return caches.match('/').then(r => r || fetch(req).catch(()=> caches.match('/')));
      return fetch(req).then(res => {
        // runtime cache successful same-origin responses
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
        }
        return res;
      }).catch(() => {
        // offline fallback for navigations — always serve "/"
        if (req.headers.get('accept')?.includes('text/html')) return caches.match('/').then(r => r || caches.match('/index.html'));
      });
    })
  );
});
