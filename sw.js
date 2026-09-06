// Nalvar PWA — offline shell cache
const CACHE = 'nalvar-v19';
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  // optimized images — precache small set for offline
  './images/optimized/appar-800.webp',
  './images/optimized/sambandar-800.webp',
  './images/optimized/sundarar-800.webp',
  './images/optimized/manickavasagar-800.webp',
  './images/siva_with_nandi_transparent.webp',
  './images/siva_with_nandi_transparent-350w.webp',
  './images/siva_with_nandi_transparent-525w.webp',
  './data.json',
  './remedies.json',
  './remedy-sources.md',
  './images/nalvar-badge-280.webp',
  './images/nalvar-badge-360.webp',
  './images/nalvar-badge-480.webp',
  './images/nalvar-transparent.webp'
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
  e.respondWith(
    caches.match(req).then(hit => {
      if (hit) return hit;
      return fetch(req).then(res => {
        // runtime cache successful same-origin responses
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
        }
        return res;
      }).catch(() => {
        // offline fallback for navigations
        if (req.headers.get('accept')?.includes('text/html')) return caches.match('./index.html');
      });
    })
  );
});
