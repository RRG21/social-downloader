self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", () => {
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  // IMPORTANT: No caching to avoid breaking yt-dlp downloads
  event.respondWith(fetch(event.request));
});