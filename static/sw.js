// SoundWave Progressive Web App Service Worker - V40 Auto-Purge
const CACHE_NAME = 'soundwave-cache-v40';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((k) => caches.delete(k))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    // Direct network streaming for audio/video/API
    if (event.request.url.includes('/api/') || 
        event.request.url.includes('.mp4') || 
        event.request.url.includes('.m4a') || 
        event.request.url.includes('saavncdn') || 
        event.request.url.includes('googlevideo') ||
        event.request.url.includes('facebook') ||
        event.request.url.includes('youtube')) {
        return;
    }
    // Network-first strategy so code updates are instant
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
