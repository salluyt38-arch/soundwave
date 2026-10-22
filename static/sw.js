// SoundWave Progressive Web App Service Worker
const CACHE_NAME = 'soundwave-cache-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    // Let audio and dynamic API calls stream directly from network
    if (event.request.url.includes('/api/') || event.request.url.includes('.mp4') || event.request.url.includes('.m4a') || event.request.url.includes('saavncdn')) {
        return;
    }
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
