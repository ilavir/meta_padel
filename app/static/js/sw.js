const CACHE_NAME = 'my-flask-pwa-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',  // Add your CSS files
    '/static/js/pwa.js',     // Add your JS files
    '/static/img/pwa/icon-192x192.png',
    '/static/img/pwa/icon-512x512.png',
    '/static/manifest.json'
];

// Install the service worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(urlsToCache);
            })
    );
});

// Cache and serve assets
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
    );
});

// Update the service worker and clean old caches
self.addEventListener('activate', event => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (!cacheWhitelist.includes(cacheName)) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});