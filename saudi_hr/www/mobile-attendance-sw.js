const CACHE_NAME = "saudi-hr-mobile-v6";

self.addEventListener("install", (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) =>
			cache.addAll([
				"/mobile-attendance",
				"/manifest.webmanifest",
				"/mobile-attendance-icon.svg",
				"/favicon.svg",
			])
		)
	);
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
		)
	);
	self.clients.claim();
});

self.addEventListener("fetch", (event) => {
	if (event.request.method !== "GET") {
		return;
	}

	if (event.request.mode === "navigate" || event.request.url.includes("/mobile-attendance")) {
		event.respondWith(
			fetch(event.request)
				.then((networkResponse) => {
					if (networkResponse && networkResponse.status === 200) {
						const responseToCache = networkResponse.clone();
						caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
					}
					return networkResponse;
				})
				.catch(() => caches.match(event.request).then((cached) => cached || caches.match("/mobile-attendance")))
		);
		return;
	}

	event.respondWith(
		caches.match(event.request).then((cachedResponse) => {
			if (cachedResponse) {
				return cachedResponse;
			}

			return fetch(event.request)
				.then((networkResponse) => {
					if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
						return networkResponse;
					}

					const responseToCache = networkResponse.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseToCache));
					return networkResponse;
				})
				.catch(() => caches.match("/mobile-attendance"));
		})
	);
});