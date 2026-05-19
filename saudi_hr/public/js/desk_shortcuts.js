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
})();
