const SAUDI_MOBILE_CACHE_PREFIX = "saudi-hr-mobile-";
const CACHE_NAME = "saudi-hr-mobile-v7";
const MOBILE_ATTENDANCE_PATH = "/mobile-attendance";
const PRECACHE_URLS = [
	MOBILE_ATTENDANCE_PATH,
	"/manifest.webmanifest",
	"/mobile-attendance-icon.svg",
	"/favicon.svg",
];
const PRECACHE_PATHS = new Set(PRECACHE_URLS);

self.addEventListener("install", (event) => {
	event.waitUntil(
		Promise.all([
			caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)),
			self.skipWaiting(),
		])
	);
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		Promise.all([
			caches.keys().then((keys) =>
				Promise.all(
					keys
						.filter(
							(key) =>
								key.startsWith(SAUDI_MOBILE_CACHE_PREFIX) && key !== CACHE_NAME
						)
						.map((key) => caches.delete(key))
				)
			),
			self.clients.claim(),
		])
	);
});

self.addEventListener("fetch", (event) => {
	if (event.request.method !== "GET") {
		return;
	}

	const url = new URL(event.request.url);
	if (url.origin !== self.location.origin) {
		return;
	}

	const is_mobile_attendance_navigation =
		event.request.mode === "navigate" &&
		(url.pathname === MOBILE_ATTENDANCE_PATH ||
			url.pathname === `${MOBILE_ATTENDANCE_PATH}/`);

	if (is_mobile_attendance_navigation) {
		event.respondWith(
			fetch(event.request)
				.then((networkResponse) => {
					if (
						networkResponse &&
						networkResponse.ok &&
						networkResponse.type === "basic"
					) {
						const responseToCache = networkResponse.clone();
						caches
							.open(CACHE_NAME)
							.then((cache) => cache.put(MOBILE_ATTENDANCE_PATH, responseToCache));
					}
					return networkResponse;
				})
				.catch(
					() =>
						caches.match(MOBILE_ATTENDANCE_PATH).then((cached) => cached || Response.error())
				)
		);
		return;
	}

	if (!PRECACHE_PATHS.has(url.pathname)) {
		return;
	}

	event.respondWith(
		caches.match(url.pathname).then((cachedResponse) => {
			if (cachedResponse) {
				return cachedResponse;
			}

			return fetch(event.request)
				.then((networkResponse) => {
					if (
						!networkResponse ||
						!networkResponse.ok ||
						networkResponse.type !== "basic"
					) {
						return networkResponse;
					}

					const responseToCache = networkResponse.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(url.pathname, responseToCache));
					return networkResponse;
				})
				.catch(() => Response.error());
		})
	);
});
