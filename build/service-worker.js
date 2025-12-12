// Service Worker for caching VietMap tiles
const CACHE_NAME = 'vietmap-tiles-v1';
const TILE_CACHE_SIZE = 500; // Max tiles to cache

// URLs to cache
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Fetch event - Cache tiles
self.addEventListener('fetch', (event) => {
  const url = event.request.url;
  
  // Cache VietMap tiles
  if (url.includes('maps.vietmap.vn')) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response) {
            // Return cached tile
            return response;
          }
          
          // Fetch and cache new tile
          return fetch(event.request).then((response) => {
            // Only cache successful responses
            if (response && response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          });
        });
      })
    );
  } else {
    // Normal fetch for other requests
    event.respondWith(fetch(event.request));
  }
});

// Activate event - Clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
