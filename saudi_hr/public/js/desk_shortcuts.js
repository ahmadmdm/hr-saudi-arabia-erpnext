(function cleanup_legacy_saudi_mobile_worker() {
	const SAUDI_MOBILE_WORKER_PATH = "/mobile-attendance-sw.js";
	const SAUDI_MOBILE_CACHE_PREFIX = "saudi-hr-mobile-";
	const SAUDI_MOBILE_CACHE_NAME = "saudi-hr-mobile-v7";
	const RELOAD_GUARD_KEY = "saudi_hr_legacy_mobile_worker_reloaded";

	function hasSaudiMobileWorker(registration) {
		return [registration.active, registration.waiting, registration.installing]
			.filter(Boolean)
			.some((worker) => {
				try {
					return new URL(worker.scriptURL).pathname === SAUDI_MOBILE_WORKER_PATH;
				} catch (error) {
					return false;
				}
			});
	}

	async function cleanup() {
		if (!("serviceWorker" in navigator)) {
			return;
		}

		const controllerIsLegacySaudiWorker = (() => {
			try {
				return (
					navigator.serviceWorker.controller &&
					new URL(navigator.serviceWorker.controller.scriptURL).pathname ===
						SAUDI_MOBILE_WORKER_PATH
				);
			} catch (error) {
				return false;
			}
		})();

		const registrations = await navigator.serviceWorker.getRegistrations();
		const legacyRegistrations = registrations.filter((registration) => {
			try {
				return new URL(registration.scope).pathname === "/" && hasSaudiMobileWorker(registration);
			} catch (error) {
				return false;
			}
		});

		const unregisterResults = await Promise.all(
			legacyRegistrations.map((registration) => registration.unregister())
		);

		if ("caches" in window) {
			const cacheNames = await caches.keys();
			await Promise.all(
				cacheNames
					.filter(
						(cacheName) =>
							cacheName.startsWith(SAUDI_MOBILE_CACHE_PREFIX) &&
							cacheName !== SAUDI_MOBILE_CACHE_NAME
					)
					.map((cacheName) => caches.delete(cacheName))
			);
		}

		const removedLegacyRegistration = unregisterResults.some(Boolean);
		if (
			controllerIsLegacySaudiWorker &&
			removedLegacyRegistration &&
			sessionStorage.getItem(RELOAD_GUARD_KEY) !== "1"
		) {
			sessionStorage.setItem(RELOAD_GUARD_KEY, "1");
			window.location.reload();
			return;
		}

		sessionStorage.removeItem(RELOAD_GUARD_KEY);
	}

	cleanup().catch(() => {
		// The desk remains usable even when browser privacy controls block PWA storage APIs.
	});
})();

(function () {
	const MOBILE_ATTENDANCE_LABEL = "\u0627\u0644\u062d\u0636\u0648\u0631 \u0639\u0628\u0631 \u0627\u0644\u062c\u0648\u0627\u0644";
	const MOBILE_ATTENDANCE_ROUTE = "/mobile-attendance";

	function is_mobile_attendance_target(target) {
		const shortcut = target.closest && target.closest(".shortcut-widget-box");
		if (shortcut && shortcut.getAttribute("aria-label") === MOBILE_ATTENDANCE_LABEL) {
			return true;
		}

		const link = target.closest && target.closest("a[href='/desk/mobile-attendance']");
		return Boolean(link);
	}

	function open_mobile_attendance(event) {
		if (!is_mobile_attendance_target(event.target)) {
			return;
		}

		event.preventDefault();
		event.stopPropagation();
		window.location.href = MOBILE_ATTENDANCE_ROUTE;
	}

	document.addEventListener("click", open_mobile_attendance, true);
	document.addEventListener(
		"keydown",
		function (event) {
			if (event.key !== "Enter" && event.key !== " ") {
				return;
			}
			open_mobile_attendance(event);
		},
		true
	);

	const ARABIC_AUTOCOMPLETE_STATUS = {
		"Begin typing for results.": "ابدأ الكتابة لعرض النتائج.",
		"No results found": "لم يتم العثور على نتائج.",
	};

	function localize_autocomplete_status(root) {
		(root || document).querySelectorAll(".tooltip-content").forEach(function (tooltip) {
			if ((tooltip.textContent || "").trim() === "undefined") {
				tooltip.textContent = "";
				tooltip.setAttribute("aria-hidden", "true");
			}
		});
		if (document.documentElement.lang !== "ar") {
			return;
		}
		(root || document).querySelectorAll(".awesomplete [role='status']").forEach(function (status) {
			const text = (status.textContent || "").trim();
			if (ARABIC_AUTOCOMPLETE_STATUS[text]) {
				status.textContent = ARABIC_AUTOCOMPLETE_STATUS[text];
			} else if (/^Type \d+ or more characters for results\.$/.test(text)) {
				const count = text.match(/\d+/)[0];
				status.textContent = `اكتب ${count} أحرف أو أكثر لعرض النتائج.`;
			} else if (/^\d+ results found$/.test(text)) {
				const count = text.match(/\d+/)[0];
				status.textContent = `تم العثور على ${count} نتيجة.`;
			}
		});
	}

	function initialize_arabic_accessibility() {
		localize_autocomplete_status(document);
		let localization_scheduled = false;
		new MutationObserver(function () {
			if (localization_scheduled) {
				return;
			}
			localization_scheduled = true;
			window.requestAnimationFrame(function () {
				localization_scheduled = false;
				localize_autocomplete_status(document);
			});
		}).observe(document.body, { childList: true, subtree: true, characterData: true });
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", initialize_arabic_accessibility);
	} else {
		initialize_arabic_accessibility();
	}
})();
